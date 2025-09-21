import signal
import sys
import time

from django.core.management.base import BaseCommand

from apps.jobs.schedulers import JobSchedulerService
from apps.langchain_integration.services.nfe_job_manager import NFEJobManager


class Command(BaseCommand):
    help = "Inicia o sistema de jobs NFE Fazenda"

    def add_arguments(self, parser):
        parser.add_argument(
            "--daemon",
            action="store_true",
            help="Executar em modo daemon (background)",
        )
        parser.add_argument(
            "--setup-only",
            action="store_true",
            help="Apenas configurar os jobs sem manter o processo ativo",
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("🚀 Iniciando sistema de jobs NFE Fazenda...")
        )

        # Configurar signal handlers para parada limpa
        def signal_handler(sig, frame):
            self.stdout.write(self.style.WARNING("\n🛑 Parando jobs..."))
            JobSchedulerService.shutdown()
            self.stdout.write(self.style.SUCCESS("✅ Jobs parados"))
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Iniciar scheduler
            JobSchedulerService.start()
            self.stdout.write(self.style.SUCCESS("✅ Scheduler iniciado"))

            # Configurar jobs
            job_manager = NFEJobManager()
            result = job_manager.setup_default_jobs()

            # Mostrar resultados
            success_count = sum(1 for v in result.values() if v == "configured")
            total_jobs = len([k for k in result.keys() if k != "errors"])

            if success_count == total_jobs:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"📋 Jobs configurados: {success_count}/{total_jobs}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"📋 Jobs configurados: {success_count}/{total_jobs}"
                    )
                )

            # Mostrar jobs configurados
            jobs = JobSchedulerService.list_jobs()
            if jobs:
                self.stdout.write("\n📅 Jobs agendados:")
                for job in jobs:
                    next_run = (
                        job.next_run_time.strftime("%d/%m/%Y %H:%M:%S")
                        if job.next_run_time
                        else "N/A"
                    )
                    self.stdout.write(f"  • {job.id}")
                    self.stdout.write(f"    Próxima execução: {next_run}")

            if result["errors"]:
                self.stdout.write(self.style.ERROR("\n❌ Erros encontrados:"))
                for error in result["errors"]:
                    self.stdout.write(self.style.ERROR(f"  - {error}"))

            # Modo setup-only
            if options["setup_only"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        "\n✅ Jobs configurados! Use --daemon ou omita --setup-only para manter ativo."
                    )
                )
                return

            # Modo daemon ou interativo
            if options["daemon"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        "🔄 Modo daemon ativo - jobs rodando em background"
                    )
                )
                self.stdout.write("ℹ️  Para parar, envie SIGTERM ao processo")
                while True:
                    time.sleep(3600)  # Check every hour
                    if not JobSchedulerService.is_running():
                        self.stdout.write(
                            self.style.ERROR("❌ Scheduler parou inesperadamente!")
                        )
                        break
            else:
                self.stdout.write(
                    self.style.SUCCESS("⏳ Pressione Ctrl+C para parar...")
                )
                last_check = None
                while True:
                    time.sleep(60)
                    current_time = time.strftime("%H:%M:%S")
                    active_jobs = len(JobSchedulerService.list_jobs())

                    if current_time != last_check:
                        self.stdout.write(
                            f"🕐 {current_time} - {active_jobs} jobs ativos | Scheduler: {'🟢' if JobSchedulerService.is_running() else '🔴'}"
                        )
                        last_check = current_time

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro: {str(e)}"))
            JobSchedulerService.shutdown()
            return

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n🛑 Interrompido pelo usuário"))
            JobSchedulerService.shutdown()
            self.stdout.write(self.style.SUCCESS("✅ Jobs parados"))
