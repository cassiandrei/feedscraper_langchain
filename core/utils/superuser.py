"""
Superuser Utilities - Design Pattern Implementation

Utilitários para criação programática de superusuários seguindo boas práticas
de design patterns. Esta é uma versão simplificada para uso em scripts e
inicialização do projeto.

Exemplo de uso:
    from core.utils.superuser import SuperuserManager

    manager = SuperuserManager()
    result = manager.create_default_superuser()
    if result.success:
        print(f"Superusuário criado: {result.user.username}")
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)


@dataclass
class SuperuserResult:
    """Resultado de operações com superusuário."""

    success: bool
    user: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
    created: bool = False


class SuperuserManager:
    """Manager para operações com superusuários usando design patterns."""

    def __init__(self):
        self.default_credentials = {
            "username": "admin",
            "email": "admin@localhost",
            "password": "admin123",
        }

    def create_superuser(
        self, username: str, email: str, password: str, force: bool = False
    ) -> SuperuserResult:
        """
        Cria um superusuário com as credenciais fornecidas.

        Args:
            username: Nome de usuário
            email: Email do usuário
            password: Senha do usuário
            force: Se True, ignora verificações de duplicata

        Returns:
            SuperuserResult com o resultado da operação
        """
        try:
            # Validações básicas
            if not username or not email or not password:
                return SuperuserResult(
                    success=False, error="Username, email e password são obrigatórios"
                )

            if len(password) < 8:
                return SuperuserResult(
                    success=False, error="Password deve ter pelo menos 8 caracteres"
                )

            # Verificar se username já existe
            if not force and User.objects.filter(username=username).exists():
                existing_user = User.objects.get(username=username)
                return SuperuserResult(
                    success=True,
                    user=existing_user,
                    message=f"Usuário '{username}' já existe",
                    created=False,
                )

            # Verificar se email já existe
            if not force and User.objects.filter(email=email).exists():
                return SuperuserResult(
                    success=False, error=f"Email '{email}' já está em uso"
                )

            # Criar superusuário
            user = User.objects.create_superuser(
                username=username, email=email, password=password
            )

            logger.info(f"Superusuário criado: {username} ({email})")

            return SuperuserResult(
                success=True,
                user=user,
                message=f"Superusuário '{username}' criado com sucesso",
                created=True,
            )

        except ValidationError as e:
            error_msg = f"Erro de validação: {e}"
            logger.error(error_msg)
            return SuperuserResult(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Erro ao criar superusuário: {e}"
            logger.error(error_msg)
            return SuperuserResult(success=False, error=error_msg)

    def create_default_superuser(self, force: bool = False) -> SuperuserResult:
        """
        Cria um superusuário com credenciais padrão.

        Args:
            force: Se True, ignora verificações de duplicata

        Returns:
            SuperuserResult com o resultado da operação
        """
        return self.create_superuser(
            username=self.default_credentials["username"],
            email=self.default_credentials["email"],
            password=self.default_credentials["password"],
            force=force,
        )

    def get_or_create_superuser(
        self, username: str, email: str, password: str
    ) -> SuperuserResult:
        """
        Obtém um superusuário existente ou cria um novo.

        Args:
            username: Nome de usuário
            email: Email do usuário
            password: Senha do usuário (usado apenas se criando)

        Returns:
            SuperuserResult com o resultado da operação
        """
        try:
            # Tentar obter usuário existente
            user = User.objects.get(username=username)
            return SuperuserResult(
                success=True,
                user=user,
                message=f"Superusuário '{username}' já existe",
                created=False,
            )

        except User.DoesNotExist:
            # Criar novo usuário
            return self.create_superuser(username, email, password, force=False)

    def ensure_default_superuser_exists(self) -> SuperuserResult:
        """
        Garante que existe pelo menos um superusuário padrão.
        Útil para inicialização do projeto.

        Returns:
            SuperuserResult com o resultado da operação
        """
        return self.get_or_create_superuser(
            username=self.default_credentials["username"],
            email=self.default_credentials["email"],
            password=self.default_credentials["password"],
        )

    def list_superusers(self) -> list:
        """
        Lista todos os superusuários existentes.

        Returns:
            Lista de usuários superusuários
        """
        return list(User.objects.filter(is_superuser=True))

    def count_superusers(self) -> int:
        """
        Conta quantos superusuários existem.

        Returns:
            Número de superusuários
        """
        return User.objects.filter(is_superuser=True).count()

    def has_superusers(self) -> bool:
        """
        Verifica se existem superusuários.

        Returns:
            True se existem superusuários, False caso contrário
        """
        return self.count_superusers() > 0


# Instância global para facilitar uso
superuser_manager = SuperuserManager()
