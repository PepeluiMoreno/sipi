"""
Scheduler para sincronización automática de OSM
Ejecuta el agente periódicamente para mantener datos actualizados
"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db.database import SessionLocal
from osm_sync_agent import OSMChurchSyncAgent

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OSMSyncScheduler:
    """Gestor de sincronizaciones programadas"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.running = False
        
    async def sync_job(self):
        """Job de sincronización que se ejecuta periódicamente"""
        logger.info("🔄 Iniciando sincronización programada de OSM")
        
        db = SessionLocal()
        try:
            agent = OSMChurchSyncAgent(db)
            
            # Sincronizar España completa usando área ISO
            logger.info("📍 Sincronizando España completa (área ISO)...")
            stats = await agent.sync_churches(
                use_spain_area=True,
                dry_run=False
            )
            
            logger.info(f"✅ Sincronización completada: {stats}")
            
            # Opción alternativa: Por provincias específicas
            # provincias = ["Madrid", "Barcelona", "Sevilla", ...]
            # for provincia in provincias:
            #     logger.info(f"📍 Sincronizando {provincia}...")
            #     stats = await agent.sync_churches(
            #         provincia_nombre=provincia,
            #         dry_run=False
            #     )
            #     logger.info(f"✅ {provincia}: {stats}")
            
        except Exception as e:
            logger.error(f"❌ Error en sincronización programada: {e}", exc_info=True)
        finally:
            db.close()
    
    def start(self):
        """Inicia el scheduler"""
        if self.running:
            logger.warning("Scheduler ya está ejecutándose")
            return
        
        # Configurar jobs
        
        # Job 1: Sincronización semanal completa (Domingos 2 AM)
        self.scheduler.add_job(
            self.sync_job,
            trigger=CronTrigger(day_of_week='sun', hour=2, minute=0),
            id='weekly_full_sync',
            name='Sincronización semanal completa',
            replace_existing=True
        )
        
        # Job 2: Sincronización incremental diaria (todos los días 3 AM)
        # Solo actualiza elementos que cambiaron
        self.scheduler.add_job(
            self.sync_job,
            trigger=CronTrigger(hour=3, minute=0),
            id='daily_incremental_sync',
            name='Sincronización incremental diaria',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.running = True
        
        logger.info("✅ Scheduler iniciado")
        logger.info("Jobs configurados:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.name}: {job.trigger}")
    
    def stop(self):
        """Detiene el scheduler"""
        if not self.running:
            logger.warning("Scheduler no está ejecutándose")
            return
        
        self.scheduler.shutdown()
        self.running = False
        logger.info("🛑 Scheduler detenido")
    
    def list_jobs(self):
        """Lista jobs configurados"""
        jobs = self.scheduler.get_jobs()
        print("\nJobs programados:")
        for job in jobs:
            print(f"  ID: {job.id}")
            print(f"  Nombre: {job.name}")
            print(f"  Trigger: {job.trigger}")
            print(f"  Próxima ejecución: {job.next_run_time}")
            print()


async def main():
    """Función principal para ejecutar el scheduler"""
    scheduler = OSMSyncScheduler()
    
    try:
        scheduler.start()
        
        # Mostrar información
        scheduler.list_jobs()
        
        logger.info("Scheduler ejecutándose. Presiona Ctrl+C para detener.")
        
        # Mantener el programa ejecutándose
        while True:
            await asyncio.sleep(3600)  # Dormir 1 hora
            
    except KeyboardInterrupt:
        logger.info("Señal de interrupción recibida")
    finally:
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
