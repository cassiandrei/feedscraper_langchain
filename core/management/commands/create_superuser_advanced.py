"""
Django Management Command - Create Superuser with Design Patterns

Este comando implementa padrões de design para criar superusuários Django:
- Command Pattern: Para encapsular operações de criação
- Strategy Pattern: Para diferentes estratégias de criação (auto/interativo)
- Builder Pattern: Para construção flexível de usuários
- Factory Pattern: Para criação de diferentes tipos de usuários
- Facade Pattern: Para simplificar a interface complexa

Uso:
    python manage.py create_superuser_advanced                          # Modo interativo
    python manage.py create_superuser_advanced --auto                   # Modo automático
    python manage.py create_superuser_advanced --username admin --email admin@test.com --password admin123
    python manage.py create_superuser_advanced --check                  # Verificar existentes
"""

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from getpass import getpass
from typing import Any, Dict, Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

User = get_user_model()


# ============================================================================
# DATA CLASSES & MODELS
# ============================================================================


@dataclass
class UserCredentials:
    """Value object para credenciais do usuário."""

    username: str
    email: str
    password: str

    def validate(self) -> bool:
        """Valida as credenciais."""
        return (
            bool(self.username and self.username.strip())
            and bool(self.email and self.email.strip())
            and bool(self.password and len(self.password) >= 8)
        )


@dataclass
class UserCreationResult:
    """Resultado da criação do usuário."""

    success: bool
    user: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None


# ============================================================================
# BUILDER PATTERN - Para construção flexível de usuários
# ============================================================================


class UserBuilder:
    """Builder para construção de usuários com validação."""

    def __init__(self):
        self.reset()

    def reset(self) -> "UserBuilder":
        """Reseta o builder para um novo usuário."""
        self._credentials = UserCredentials("", "", "")
        return self

    def with_username(self, username: str) -> "UserBuilder":
        """Define o username."""
        self._credentials.username = username.strip()
        return self

    def with_email(self, email: str) -> "UserBuilder":
        """Define o email."""
        self._credentials.email = email.strip()
        return self

    def with_password(self, password: str) -> "UserBuilder":
        """Define a senha."""
        self._credentials.password = password
        return self

    def build(self) -> UserCredentials:
        """Constrói as credenciais do usuário."""
        if not self._credentials.validate():
            raise ValueError("Credenciais inválidas")
        return self._credentials


# ============================================================================
# STRATEGY PATTERN - Para diferentes estratégias de criação
# ============================================================================


class UserInputStrategy(ABC):
    """Interface para estratégias de entrada de dados do usuário."""

    @abstractmethod
    def get_credentials(self, stdout) -> UserCredentials:
        """Obtém as credenciais do usuário."""
        pass


class InteractiveInputStrategy(UserInputStrategy):
    """Estratégia de entrada interativa."""

    def get_credentials(self, stdout) -> UserCredentials:
        """Solicita credenciais interativamente."""
        stdout.write("📝 Criação de Superusuário - Modo Interativo")
        stdout.write("-" * 50)

        builder = UserBuilder()

        # Username
        while True:
            username = input("Username: ").strip()
            if username:
                builder.with_username(username)
                break
            stdout.write("❌ Username não pode estar vazio!")

        # Email
        while True:
            email = input("Email: ").strip()
            if email:
                builder.with_email(email)
                break
            stdout.write("❌ Email não pode estar vazio!")

        # Password
        while True:
            password = getpass("Password: ").strip()
            if len(password) >= 8:
                confirm = getpass("Password (confirmação): ").strip()
                if password == confirm:
                    builder.with_password(password)
                    break
                else:
                    stdout.write("❌ Passwords não coincidem!")
            else:
                stdout.write("❌ Password deve ter pelo menos 8 caracteres!")

        return builder.build()


class AutomaticInputStrategy(UserInputStrategy):
    """Estratégia de entrada automática com valores padrão."""

    def __init__(
        self,
        username: str = "admin",
        email: str = "admin@localhost",
        password: str = "admin123",
    ):
        self._builder = UserBuilder()
        self._builder.with_username(username).with_email(email).with_password(password)

    def get_credentials(self, stdout) -> UserCredentials:
        """Retorna credenciais pré-configuradas."""
        stdout.write("🤖 Criação de Superusuário - Modo Automático")
        stdout.write("-" * 50)
        credentials = self._builder.build()
        stdout.write(f"Username: {credentials.username}")
        stdout.write(f"Email: {credentials.email}")
        stdout.write(f"Password: {'*' * len(credentials.password)}")
        return credentials


class ParameterInputStrategy(UserInputStrategy):
    """Estratégia de entrada via parâmetros."""

    def __init__(self, username: str, email: str, password: str):
        self._builder = UserBuilder()
        self._builder.with_username(username).with_email(email).with_password(password)

    def get_credentials(self, stdout) -> UserCredentials:
        """Retorna credenciais dos parâmetros."""
        return self._builder.build()


# ============================================================================
# FACTORY PATTERN - Para criação de estratégias
# ============================================================================


class InputStrategyFactory:
    """Factory para criação de estratégias de entrada."""

    @staticmethod
    def create_interactive_strategy() -> UserInputStrategy:
        """Cria estratégia interativa."""
        return InteractiveInputStrategy()

    @staticmethod
    def create_automatic_strategy(
        username: str = "admin",
        email: str = "admin@localhost",
        password: str = "admin123",
    ) -> UserInputStrategy:
        """Cria estratégia automática."""
        return AutomaticInputStrategy(username, email, password)

    @staticmethod
    def create_parameter_strategy(
        username: str, email: str, password: str
    ) -> UserInputStrategy:
        """Cria estratégia por parâmetros."""
        return ParameterInputStrategy(username, email, password)


# ============================================================================
# COMMAND PATTERN - Para encapsular operações
# ============================================================================


class SuperuserCommand(ABC):
    """Interface base para comandos."""

    @abstractmethod
    def execute(self) -> UserCreationResult:
        """Executa o comando."""
        pass


class CreateSuperuserCommand(SuperuserCommand):
    """Comando para criar superusuário."""

    def __init__(self, credentials: UserCredentials):
        self._credentials = credentials

    def execute(self) -> UserCreationResult:
        """Executa a criação do superusuário."""
        try:
            # Verificar se username já existe
            if User.objects.filter(username=self._credentials.username).exists():
                return UserCreationResult(
                    success=False,
                    error=f"Usuário '{self._credentials.username}' já existe!",
                )

            # Verificar se email já existe
            if User.objects.filter(email=self._credentials.email).exists():
                return UserCreationResult(
                    success=False,
                    error=f"Email '{self._credentials.email}' já está em uso!",
                )

            # Criar superusuário
            user = User.objects.create_superuser(
                username=self._credentials.username,
                email=self._credentials.email,
                password=self._credentials.password,
            )

            return UserCreationResult(
                success=True, user=user, message="Superusuário criado com sucesso!"
            )

        except ValidationError as e:
            return UserCreationResult(success=False, error=f"Erro de validação: {e}")
        except Exception as e:
            return UserCreationResult(
                success=False, error=f"Erro ao criar superusuário: {e}"
            )


class CheckExistingSuperusersCommand(SuperuserCommand):
    """Comando para verificar superusuários existentes."""

    def execute(self) -> UserCreationResult:
        """Lista superusuários existentes."""
        superusers = User.objects.filter(is_superuser=True)
        if superusers.exists():
            message = "🔍 Superusuários existentes:\n"
            for user in superusers:
                message += f"   - {user.username} ({user.email})\n"
            return UserCreationResult(success=True, message=message.strip())
        return UserCreationResult(
            success=True, message="Nenhum superusuário encontrado."
        )


# ============================================================================
# FACADE PATTERN - Interface simplificada
# ============================================================================


class SuperuserCreatorFacade:
    """Facade que simplifica a criação de superusuários."""

    def __init__(self):
        self._factory = InputStrategyFactory()

    def create_superuser_interactive(
        self, stdout, force: bool = False
    ) -> UserCreationResult:
        """Cria superusuário interativamente."""
        return self._create_with_strategy(
            self._factory.create_interactive_strategy(), stdout, force
        )

    def create_superuser_automatic(
        self, stdout, force: bool = False
    ) -> UserCreationResult:
        """Cria superusuário automaticamente."""
        return self._create_with_strategy(
            self._factory.create_automatic_strategy(), stdout, force
        )

    def create_superuser_with_params(
        self, username: str, email: str, password: str, stdout, force: bool = False
    ) -> UserCreationResult:
        """Cria superusuário com parâmetros específicos."""
        return self._create_with_strategy(
            self._factory.create_parameter_strategy(username, email, password),
            stdout,
            force,
        )

    def check_existing_superusers(self) -> UserCreationResult:
        """Verifica superusuários existentes."""
        command = CheckExistingSuperusersCommand()
        return command.execute()

    def _create_with_strategy(
        self, strategy: UserInputStrategy, stdout, force: bool
    ) -> UserCreationResult:
        """Cria superusuário usando a estratégia fornecida."""
        try:
            credentials = strategy.get_credentials(stdout)
            command = CreateSuperuserCommand(credentials)
            return command.execute()
        except Exception as e:
            return UserCreationResult(
                success=False, error=f"Erro na estratégia de entrada: {e}"
            )


# ============================================================================
# DJANGO MANAGEMENT COMMAND
# ============================================================================


class Command(BaseCommand):
    """Comando Django para criação avançada de superusuários com design patterns."""

    help = "Cria superusuário usando padrões de design avançados"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.facade = SuperuserCreatorFacade()

    def add_arguments(self, parser):
        """Adiciona argumentos ao comando."""
        parser.add_argument(
            "--auto",
            action="store_true",
            help="Modo automático com credenciais padrão (admin/admin@localhost/admin123)",
        )

        parser.add_argument("--username", type=str, help="Username do superusuário")

        parser.add_argument("--email", type=str, help="Email do superusuário")

        parser.add_argument("--password", type=str, help="Password do superusuário")

        parser.add_argument(
            "--check", action="store_true", help="Verificar superusuários existentes"
        )

        parser.add_argument(
            "--force",
            action="store_true",
            help="Forçar criação mesmo que existam conflitos",
        )

    def handle(self, *args, **options):
        """Executa o comando."""
        self.stdout.write("=" * 60)
        self.stdout.write(
            self.style.SUCCESS("🚀 Django Superuser Creator - Design Patterns Edition")
        )
        self.stdout.write("=" * 60)

        # Verificar superusuários existentes se solicitado
        if options["check"]:
            result = self.facade.check_existing_superusers()
            self._display_result(result)
            return

        # Determinar modo de operação
        if options["auto"]:
            result = self.facade.create_superuser_automatic(
                self.stdout, options.get("force", False)
            )
        elif options["username"] and options["email"] and options["password"]:
            result = self.facade.create_superuser_with_params(
                options["username"],
                options["email"],
                options["password"],
                self.stdout,
                options.get("force", False),
            )
        else:
            result = self.facade.create_superuser_interactive(
                self.stdout, options.get("force", False)
            )

        self._display_result(result)

    def _display_result(self, result: UserCreationResult):
        """Exibe o resultado da operação."""
        self.stdout.write("\n" + "=" * 60)

        if result.success:
            self.stdout.write(self.style.SUCCESS(f"✅ {result.message}"))
            if result.user:
                self.stdout.write(f"   👤 Usuário: {result.user.username}")
                self.stdout.write(f"   📧 Email: {result.user.email}")
                self.stdout.write("\n💡 Você pode agora acessar o Django Admin em:")
                self.stdout.write("   http://127.0.0.1:8000/admin/")
        else:
            self.stdout.write(self.style.ERROR(f"❌ {result.error}"))

        self.stdout.write("=" * 60)
