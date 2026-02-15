import os, sys, asyncio, json, logging, re
from datetime import datetime
import redis, anthropic, httpx

logging.basicConfig(level=logging.INFO, format='%(asctime)s [BRAIN] %(levelname)s: %(message)s')
log = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", os.getenv('REDIS_HOST', '127.0.0.1'))
REDIS_PORT = int(os.getenv("REDIS_PORT", int(os.getenv('REDIS_PORT', '6379'))))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
HUE_BRIDGE_IP = os.getenv("HUE_BRIDGE_IP", os.getenv('HUE_BRIDGE_IP', '192.168.178.69'))
HUE_API_KEY = os.getenv("HUE_API_KEY", "") or os.getenv('HUE_API_KEY', 'tNZIBriUkfuBz7jvE1v9CtzrtmsdumDOgsVQI554')

SYSTEM_PROMPT = """Tu es SINIK Brain, le cerveau IA d'une maison connectée.

Tu reçois des événements réseau et tu décides des actions sur les lumières.

RÈGLES AUTOMATIQUES:
- Netflix, YouTube, Disney+, Amazon Prime → Tamiser lumières (brightness 30-50)
- Spotify, Apple Music → Ambiance colorée (colorloop ou warm)
- Twitch → Lumière gaming (couleur violette/bleue)
- Aucune activité streaming → Ne rien faire

RÉPONSE JSON UNIQUEMENT (pas de texte avant/après):
{
  "action": "dim_lights" | "lights_on" | "lights_off" | "color_scene" | "none",
  "target": "all",
  "params": {"brightness": 30, "color": "warm"},
  "reason": "Netflix détecté, mode cinéma"
}
"""

class SinikBrain:
    def __init__(self):
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
        self.hue_url = f"http://{HUE_BRIDGE_IP}/api/{HUE_API_KEY}"
        self.last_action = {}
        self.cooldown = 60
        log.info(f"Hue URL: {self.hue_url}")
        
    async def get_context(self):
        context = {"devices": [], "services": [], "time": datetime.now().strftime("%H:%M")}
        for key in self.redis.scan_iter("sinik:activity:*"):
            ip = key.split(":")[-1]
            data = self.redis.hgetall(key)
            if data:
                context["devices"].append({"ip": ip, "service": data.get("last_service")})
                if data.get("last_service"):
                    context["services"].append(data.get("last_service"))
        return context
    
    async def ask_claude(self, event, context):
        if not self.anthropic:
            log.warning("No Anthropic API key, using default action")
            service = event.get("service", "")
            if service in ["netflix", "youtube", "disney", "amazon"]:
                return {"action": "dim_lights", "target": "all", "params": {"brightness": 40}, "reason": f"{service} detected"}
            elif service in ["spotify", "apple"]:
                return {"action": "color_scene", "target": "all", "params": {"color": "warm"}, "reason": f"{service} detected"}
            return {"action": "none", "reason": "Unknown service"}
        
        prompt = f"""Événement détecté:
Service: {event.get('service')}
Device IP: {event.get('device_ip')}
Heure: {context.get('time')}
Services actifs: {context.get('services')}

Quelle action prendre?"""

        try:
            response = self.anthropic.messages.create(
                model=os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514'),
                max_tokens=300,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                decision = json.loads(match.group(0))
                log.info(f"Claude decision: {decision}")
                return decision
        except Exception as e:
            log.error(f"Claude error: {e}")
        return None
    
    async def execute_action(self, decision):
        action = decision.get("action", "none")
        if action == "none":
            log.info(f"No action: {decision.get('reason')}")
            return True
        
        params = decision.get("params", {})
        log.info(f"Executing: {action} with {params}")
        
        try:
            lock_key = "sinik:lock:lights_all"
            if not self.redis.set(lock_key, "1", nx=True, ex=10):
                log.warning("Could not acquire lock")
                return False
            
            async with httpx.AsyncClient() as client:
                if action == "dim_lights":
                    bri = params.get("brightness", 50)
                    r = await client.put(f"{self.hue_url}/groups/0/action", json={"on": True, "bri": bri})
                    log.info(f"Dim lights to {bri}: {r.status_code}")
                    
                elif action == "lights_off":
                    r = await client.put(f"{self.hue_url}/groups/0/action", json={"on": False})
                    log.info(f"Lights off: {r.status_code}")
                    
                elif action == "lights_on":
                    bri = params.get("brightness", 254)
                    r = await client.put(f"{self.hue_url}/groups/0/action", json={"on": True, "bri": bri})
                    log.info(f"Lights on: {r.status_code}")
                    
                elif action == "color_scene":
                    color = params.get("color", "warm")
                    if color == "colorloop":
                        r = await client.put(f"{self.hue_url}/groups/0/action", json={"on": True, "effect": "colorloop"})
                    elif color == "warm":
                        r = await client.put(f"{self.hue_url}/groups/0/action", json={"on": True, "ct": 400, "bri": 150})
                    elif color == "cool":
                        r = await client.put(f"{self.hue_url}/groups/0/action", json={"on": True, "ct": 200, "bri": 200})
                    elif color == "purple" or color == "gaming":
                        r = await client.put(f"{self.hue_url}/groups/0/action", json={"on": True, "hue": 50000, "sat": 254, "bri": 150})
                    log.info(f"Color scene {color}: {r.status_code}")
            
            # Store decision
            self.redis.set("sinik:dev:lights_all:target", json.dumps({
                "action": action,
                "params": params,
                "reason": decision.get("reason"),
                "timestamp": datetime.now().isoformat()
            }))
            
            self.redis.delete(lock_key)
            log.info(f"Action executed: {action}")
            return True
            
        except Exception as e:
            log.error(f"Execute error: {e}")
            return False
    
    async def process_event(self, event):
        device_ip = event.get("device_ip")
        service = event.get("service")
        
        log.info(f"{'='*50}")
        log.info(f"PROCESSING: {service} from {device_ip}")
        log.info(f"{'='*50}")
        
        # Cooldown check
        key = f"{device_ip}:{service}"
        if key in self.last_action:
            elapsed = (datetime.now() - self.last_action[key]).seconds
            if elapsed < self.cooldown:
                log.info(f"Cooldown active ({elapsed}s < {self.cooldown}s), skipping")
                return
        
        context = await self.get_context()
        log.info(f"Context: {context}")
        
        decision = await self.ask_claude(event, context)
        
        if decision:
            success = await self.execute_action(decision)
            if success:
                self.last_action[key] = datetime.now()
                self.redis.lpush("sinik:brain:decisions", json.dumps({
                    "event": event,
                    "decision": decision,
                    "timestamp": datetime.now().isoformat()
                }))
                self.redis.ltrim("sinik:brain:decisions", 0, 99)
                log.info(f"Decision logged: {decision.get('action')}")
    
    async def listen_events(self):
        pubsub = self.redis.pubsub()
        pubsub.subscribe("sinik:brain:trigger")
        log.info("="*50)
        log.info("BRAIN READY - Listening for triggers...")
        log.info("="*50)
        
        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = message["data"]
                    log.info(f"Received trigger: {data[:100]}...")
                    event = json.loads(data)
                    await self.process_event(event)
                except Exception as e:
                    log.error(f"Event error: {e}")
    
    async def run(self):
        log.info("SINIK Brain starting...")
        log.info(f"Hue Bridge: {HUE_BRIDGE_IP}")
        log.info(f"API Key: {HUE_API_KEY[:10]}...")
        
        try:
            self.redis.ping()
            log.info("Redis connected")
        except Exception as e:
            log.error(f"Redis failed: {e}")
            return
        
        log.info("Anthropic API: " + ("configured" if self.anthropic else "NOT configured"))
        await self.listen_events()

if __name__ == "__main__":
    asyncio.run(SinikBrain().run())
