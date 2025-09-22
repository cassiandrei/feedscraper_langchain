"""
Teste para o job nfe_technical_notes_processing.
Este job processa notas técnicas pendentes usando LangChain/GPT-4-mini.
"""

import os
import django

# Carregar variáveis do arquivo .env manualmente
def load_env():
    """Carrega as variáveis do arquivo .env"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.jobs.tasks import process_pending_technical_notes_job
from apps.langchain_integration.services.technical_note_processor import TechnicalNoteSummarizerService


def test_processing_service():
    """Testa a inicialização do service de processamento."""
    print("🔧 Testando TechnicalNoteSummarizerService...")
    try:
        service = TechnicalNoteSummarizerService()
        print("✅ TechnicalNoteSummarizerService inicializado com sucesso")
        
        # Verificar itens pendentes
        print("\n📋 Verificando itens pendentes...")
        pending_notes = service.get_pending_notes(limit=5)
        print(f"📊 Encontrados {len(pending_notes)} itens pendentes para processar")
        
        if pending_notes:
            print("\n📝 Itens pendentes:")
            for i, note in enumerate(pending_notes[:3]):  # Mostrar apenas os primeiros 3
                print(f"  {i+1}. {note.title[:60]}..." if len(note.title) > 60 else f"  {i+1}. {note.title}")
                print(f"     Status: {note.status}")
                print(f"     Criado em: {note.created_at}")
                print(f"     URL: {note.original_url[:50]}...")
        else:
            print("ℹ️  Nenhum item pendente encontrado. Execute primeiro o scraping para gerar dados.")
            
    except Exception as e:
        print(f"❌ Erro ao testar service: {e}")
        return False
    
    return True


def test_processing_job():
    """Testa o job de processamento."""
    print("\n🚀 Testando job nfe_technical_notes_processing...")
    
    try:
        # Executar job com limite pequeno para teste
        result = process_pending_technical_notes_job(max_items=3)
        
        print("\n📊 Resultado do processamento:")
        print(f"✅ Sucesso: {result.get('success', False)}")
        
        if result.get('success'):
            stats = result.get('stats', {})
            print(f"📈 Estatísticas:")
            print(f"  - Total: {stats.get('total', 0)}")
            print(f"  - Processados: {stats.get('processed', 0)}")
            print(f"  - Erros: {stats.get('errors', 0)}")
            print(f"  - Ignorados: {stats.get('skipped', 0)}")
            print(f"⏱️  Duração: {result.get('duration_seconds', 0):.2f} segundos")
        else:
            print(f"❌ Erro: {result.get('error', 'Erro desconhecido')}")
            
    except KeyboardInterrupt:
        print("\n✋ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro no teste do job: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Função principal do teste."""
    print("🧪 TESTE DO JOB DE PROCESSAMENTO NFE")
    print("=" * 50)
    
    # Teste 1: Service de processamento
    service_ok = test_processing_service()
    
    if service_ok:
        # Teste 2: Job de processamento
        test_processing_job()
    else:
        print("\n⚠️  Pulando teste do job devido a erro no service")
    
    print("\n✅ Teste concluído!")


if __name__ == "__main__":
    main()
