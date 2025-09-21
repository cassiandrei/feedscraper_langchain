#!/usr/bin/env python
"""
Teste rápido das correções feitas no sistema NFE.
"""
import os
import sys

import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.jobs.schedulers import JobSchedulerService
from apps.langchain_integration.services.nfe_job_manager import NFEJobManager
from apps.langchain_integration.services.technical_note_processor import (
    TechnicalNoteSummarizerService,
)


def test_services():
    """Testa os serviços básicos sem executar jobs completos."""

    print("🔧 Testando TechnicalNoteSummarizerService...")
    try:
        service = TechnicalNoteSummarizerService()
        print("✅ TechnicalNoteSummarizerService inicializado com sucesso")
    except Exception as e:
        print(f"❌ Erro ao inicializar TechnicalNoteSummarizerService: {e}")

    print("\n🔧 Testando JobSchedulerService...")
    try:
        is_running = JobSchedulerService.is_running()
        print(f"✅ JobSchedulerService.is_running(): {is_running}")
    except Exception as e:
        print(f"❌ Erro no JobSchedulerService: {e}")

    print("\n🔧 Testando NFEJobManager...")
    try:
        manager = NFEJobManager()
        status = manager.get_job_status()
        print(f"✅ NFEJobManager status: {status.get('timestamp', 'N/A')}")
    except Exception as e:
        print(f"❌ Erro no NFEJobManager: {e}")

    print("\n🎉 Teste básico concluído!")


if __name__ == "__main__":
    test_services()
