#!/usr/bin/env python
"""
Script de Inicialização do Projeto Django

Este script realiza as operações básicas de inicialização do projeto:
1. Aplica migrações do banco de dados
2. Coleta arquivos estáticos (em produção)
3. Cria superusuário padrão se não existir
4. Executa outros setup necessários

Uso:
    python scripts/init_project.py                    # Desenvolvimento
    python scripts/init_project.py --production       # Produção
    python scripts/init_project.py --force-superuser  # Força criação de superusuário
"""

import os
import sys
from pathlib import Path

import django

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

import argparse
import logging

from core.utils.superuser import superuser_manager
from django.conf import settings
from django.core.management import call_command, execute_from_command_line

logger = logging.getLogger(__name__)


class ProjectInitializer:
    """Inicializador do projeto com operações essenciais."""

    def __init__(self, production: bool = False, force_superuser: bool = False):
        self.production = production
        self.force_superuser = force_superuser
        self.setup_logging()

    def setup_logging(self):
        """Configura logging para o inicializador."""
        level = logging.INFO if not self.production else logging.WARNING
        logging.basicConfig(
            level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def run_migrations(self):
        """Aplica migrações do banco de dados."""
        print("🔄 Aplicando migrações do banco de dados...")
        try:
            call_command("migrate", verbosity=1, interactive=False)
            print("✅ Migrações aplicadas com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro ao aplicar migrações: {e}")
            return False

    def collect_static_files(self):
        """Coleta arquivos estáticos (apenas em produção)."""
        if not self.production:
            print("⏩ Pulando coleta de arquivos estáticos (modo desenvolvimento)")
            return True

        print("📦 Coletando arquivos estáticos...")
        try:
            call_command("collectstatic", verbosity=1, interactive=False, clear=True)
            print("✅ Arquivos estáticos coletados com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro ao coletar arquivos estáticos: {e}")
            return False

    def ensure_superuser(self):
        """Garante que existe um superusuário."""
        print("👤 Verificando superusuário padrão...")

        if self.force_superuser:
            result = superuser_manager.create_default_superuser(force=True)
        else:
            result = superuser_manager.ensure_default_superuser_exists()

        if result.success:
            if result.created:
                print(f"✅ Superusuário criado: {result.user.username}")
                print(f"   📧 Email: {result.user.email}")
                print("   🔐 Password: admin123")
                print("   💡 Altere a senha padrão em produção!")
            else:
                print(f"ℹ️  Superusuário já existe: {result.user.username}")
            return True
        else:
            print(f"❌ Erro ao criar superusuário: {result.error}")
            return False

    def check_database_connection(self):
        """Verifica conexão com banco de dados."""
        print("🔍 Verificando conexão com banco de dados...")
        try:
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            print("✅ Conexão com banco de dados OK!")
            return True
        except Exception as e:
            print(f"❌ Erro de conexão com banco: {e}")
            return False

    def display_project_info(self):
        """Exibe informações do projeto."""
        print("\n" + "=" * 60)
        print("📋 INFORMAÇÕES DO PROJETO")
        print("=" * 60)
        print(f"🏷️  Projeto: {getattr(settings, 'PROJECT_NAME', 'NFE Feed Scraper')}")
        print(f"🐍 Django: {django.get_version()}")
        print(f"🗃️  Database: {settings.DATABASES['default']['ENGINE'].split('.')[-1]}")
        print(f"🔧 Ambiente: {'Produção' if self.production else 'Desenvolvimento'}")
        print(f"📊 Debug: {settings.DEBUG}")

        # Contar superusuários
        superuser_count = superuser_manager.count_superusers()
        print(f"👥 Superusuários: {superuser_count}")

        if superuser_count > 0:
            superusers = superuser_manager.list_superusers()
            for user in superusers:
                print(f"   - {user.username} ({user.email})")

        print("=" * 60)

    def run(self):
        """Executa todas as operações de inicialização."""
        print("🚀 INICIALIZANDO PROJETO DJANGO")
        print("=" * 60)

        success = True

        # 1. Verificar conexão com banco
        if not self.check_database_connection():
            return False

        # 2. Aplicar migrações
        if not self.run_migrations():
            success = False

        # 3. Coletar arquivos estáticos (produção)
        if not self.collect_static_files():
            success = False

        # 4. Criar superusuário
        if not self.ensure_superuser():
            success = False

        # 5. Exibir informações do projeto
        self.display_project_info()

        if success:
            print("\n🎉 Inicialização concluída com sucesso!")
            print("💡 Você pode agora executar o servidor Django:")
            print("   python manage.py runserver")
            print("\n🌐 URLs importantes:")
            print("   Admin: http://127.0.0.1:8000/admin/")
            print("   API: http://127.0.0.1:8000/api/")
        else:
            print("\n❌ Inicialização concluída com erros!")
            print("   Verifique os logs acima para mais detalhes.")

        return success


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description="Inicializa o projeto Django com configurações essenciais",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
    python scripts/init_project.py                    # Desenvolvimento
    python scripts/init_project.py --production       # Produção
    python scripts/init_project.py --force-superuser  # Força criação
        """,
    )

    parser.add_argument(
        "--production",
        action="store_true",
        help="Executa em modo produção (coleta arquivos estáticos)",
    )

    parser.add_argument(
        "--force-superuser",
        action="store_true",
        help="Força criação do superusuário mesmo que já exista",
    )

    args = parser.parse_args()

    try:
        initializer = ProjectInitializer(
            production=args.production, force_superuser=args.force_superuser
        )
        success = initializer.run()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n❌ Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        logger.exception("Erro durante inicialização")
        sys.exit(1)


if __name__ == "__main__":
    main()
