"""
CLI para gestionar sincronización OSM
Uso: python osm_cli.py sync --provincia "Madrid" --dry-run
"""
import asyncio
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="CLI para sincronización OSM de SIPI")
console = Console()


@app.command()
def sync(
    provincia: Optional[str] = typer.Option(None, "--provincia", "-p", help="Nombre de provincia a sincronizar"),
    bbox: Optional[str] = typer.Option(None, "--bbox", "-b", help="Bounding box manual: 'min_lat,min_lon,max_lat,max_lon'"),
    spain_area: bool = typer.Option(False, "--spain-area", "-s", help="Usar área ISO de España completa (ignora provincia y bbox)"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Simular sin guardar cambios"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Salida detallada")
):
    """Sincronizar iglesias desde OpenStreetMap
    
    Modos de uso:
    1. España completa:  --spain-area
    2. Por provincia:    --provincia "Madrid"
    3. Por bbox:         --bbox "40.3,-3.8,40.5,-3.6"
    """
    
    from app.db.database import SessionLocal
    from osm_sync_agent import OSMChurchSyncAgent
    
    console.print("[bold blue]🔄 Iniciando sincronización OSM...[/bold blue]")
    
    # Convertir bbox string a tupla si existe
    bbox_tuple = None
    if bbox:
        try:
            bbox_tuple = tuple(map(float, bbox.split(",")))
            if len(bbox_tuple) != 4:
                raise ValueError("Bbox debe tener 4 valores")
        except Exception as e:
            console.print(f"[red]❌ Error en bbox: {e}[/red]")
            raise typer.Exit(1)
    
    # Modo dry-run
    if dry_run:
        console.print("[yellow]⚠️  MODO SIMULACIÓN - No se guardarán cambios[/yellow]")
    
    # Modo de operación
    if spain_area:
        console.print("[bold cyan]📍 Modo: España completa (área ISO)[/bold cyan]")
    elif provincia:
        console.print(f"[bold cyan]📍 Provincia: {provincia}[/bold cyan]")
    elif bbox:
        console.print(f"[bold cyan]📍 Área personalizada (bbox)[/bold cyan]")
    
    # Ejecutar sincronización
    db = SessionLocal()
    try:
        agent = OSMChurchSyncAgent(db)
        
        stats = asyncio.run(agent.sync_churches(
            bbox=bbox_tuple,
            provincia_nombre=provincia,
            use_spain_area=spain_area,
            dry_run=dry_run
        ))
        
        # Mostrar resultados
        if "error" in stats:
            console.print(f"[red]❌ Error: {stats['error']}[/red]")
            raise typer.Exit(1)
        
        table = Table(title="Resultados de Sincronización")
        table.add_column("Métrica", style="cyan")
        table.add_column("Cantidad", style="magenta")
        
        table.add_row("Creados", str(stats.get("created", 0)))
        table.add_row("Actualizados", str(stats.get("updated", 0)))
        table.add_row("Sin cambios", str(stats.get("skipped", 0)))
        table.add_row("Errores", str(stats.get("errors", 0)))
        
        console.print(table)
        console.print("[bold green]✅ Sincronización completada[/bold green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error fatal: {e}[/red]")
        raise typer.Exit(1)
    finally:
        db.close()


@app.command()
def list_provincias():
    """Listar provincias disponibles en la base de datos"""
    from app.db.database import SessionLocal
    from app.db.models import Provincia
    
    db = SessionLocal()
    try:
        provincias = db.query(Provincia).order_by(Provincia.nombre).all()
        
        table = Table(title="Provincias Disponibles")
        table.add_column("Nombre", style="cyan")
        table.add_column("ID", style="dim")
        
        for p in provincias:
            table.add_row(p.nombre, p.id)
        
        console.print(table)
        console.print(f"\n[bold]Total: {len(provincias)} provincias[/bold]")
        
    finally:
        db.close()


@app.command()
def stats():
    """Mostrar estadísticas de inmuebles sincronizados desde OSM"""
    from app.db.database import SessionLocal
    from app.db.models import Inmueble, InmuebleOSMExt
    from sqlalchemy import func
    
    db = SessionLocal()
    try:
        # Total inmuebles
        total_inmuebles = db.query(func.count(Inmueble.id)).scalar()
        
        # Inmuebles con datos OSM
        total_osm = db.query(func.count(InmuebleOSMExt.id)).scalar()
        
        # Última sincronización
        last_sync = db.query(func.max(InmuebleOSMExt.updated_at)).scalar()
        
        table = Table(title="Estadísticas OSM")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="magenta")
        
        table.add_row("Total Inmuebles", str(total_inmuebles))
        table.add_row("Con datos OSM", str(total_osm))
        table.add_row("Porcentaje OSM", f"{(total_osm/total_inmuebles*100):.1f}%" if total_inmuebles > 0 else "0%")
        table.add_row("Última sincronización", str(last_sync) if last_sync else "Nunca")
        
        console.print(table)
        
    finally:
        db.close()


@app.command()
def seed_tipos():
    """Poblar catálogo de tipos de inmueble para OSM"""
    from app.db.database import SessionLocal
    from app.db.models import TipoInmueble
    
    tipos_religiosos = [
        ("Catedral", "Iglesia catedral, sede de un obispado"),
        ("Basílica", "Templo con rango especial otorgado por el Papa"),
        ("Iglesia", "Templo cristiano general"),
        ("Capilla", "Templo pequeño o parte de un edificio mayor"),
        ("Ermita", "Pequeño santuario o capilla rural"),
        ("Monasterio", "Edificio habitado por monjes"),
        ("Convento", "Edificio habitado por religiosos/as"),
        ("Campanario", "Torre con campanas"),
        ("Humilladero", "Pequeño santuario en caminos"),
        ("Crucero", "Cruz monumental en encrucijadas"),
        ("Gruta", "Santuario en cavidad natural o artificial"),
        ("Santuario", "Lugar de culto con especial devoción"),
    ]
    
    db = SessionLocal()
    try:
        created = 0
        for nombre, descripcion in tipos_religiosos:
            existing = db.query(TipoInmueble).filter(
                TipoInmueble.nombre == nombre
            ).first()
            
            if not existing:
                tipo = TipoInmueble(
                    nombre=nombre,
                    descripcion=descripcion,
                    activo=True
                )
                db.add(tipo)
                created += 1
                console.print(f"[green]✓[/green] Creado: {nombre}")
            else:
                console.print(f"[yellow]→[/yellow] Ya existe: {nombre}")
        
        db.commit()
        console.print(f"\n[bold green]✅ {created} tipos creados[/bold green]")
        
    finally:
        db.close()


if __name__ == "__main__":
    app()
