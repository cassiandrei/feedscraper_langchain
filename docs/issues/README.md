# Issues Documentation

Esta pasta contém a documentação de issues específicas do projeto, seguindo o padrão PRP (Product Requirement Prompt).

## 📁 Estrutura

```
docs/issues/
├── README.md                    # Este arquivo
├── [issue_id]/                  # Pasta específica para cada issue
│   ├── prp.md                  # PRP da issue (baseado no template)
│   ├── assets/                 # Arquivos de apoio (imagens, diagramas, etc.)
│   ├── research/               # Pesquisas e análises técnicas
│   └── decisions/              # Decisões arquiteturais específicas
└── templates/
    └── issue_template.md       # Template para novas issues
```

## 🎯 Como Usar

### 1. Criar Nova Issue

Para documentar uma nova issue:

1. **Copie o template**: Use o arquivo `../PRP_ISSUE_TEMPLATE.md` como base
2. **Crie a pasta**: `docs/issues/[issue_id]/`
3. **Copie o template**: Para `docs/issues/[issue_id]/prp.md`
4. **Preencha os dados**: Substitua todos os placeholders `[SUBSTITUIR_POR_...]`

### 2. Nomenclatura de Issues

Use o padrão: `[categoria]_[resumo]`

Exemplos:
- `nfe_fazenda` - Integração com API da Fazenda para NFe
- `langchain_optimization` - Otimização do LangChain
- `job_scheduler_fix` - Correção no sistema de jobs
- `auth_system` - Sistema de autenticação

### 3. Placeholders do Template

O template `PRP_ISSUE_TEMPLATE.md` contém os seguintes placeholders que devem ser substituídos:

#### Informações Básicas
- `[SUBSTITUIR_POR_ID_DA_ISSUE]` - ID único da issue
- `[SUBSTITUIR_POR_TITULO_DA_ISSUE]` - Título descritivo
- `[SUBSTITUIR_POR_DATA]` - Data de criação
- `[SUBSTITUIR_POR_LABELS]` - Tags/labels da issue

#### Descrição
- `[DESCREVER_O_CONTEXTO_DA_ISSUE]` - Contexto e background
- `[DESCREVER_O_PROBLEMA_OU_NECESSIDADE]` - Problema atual
- `[DESCREVER_A_SOLUÇÃO_PROPOSTA]` - Solução proposta

#### Requisitos
- `[NOME_DO_REQUISITO]` - Nome do requisito funcional
- `[DESCRIÇÃO_DETALHADA]` - Descrição detalhada do requisito
- `[CRITERIO_X]` - Critérios de aceitação específicos

#### Implementação
- `[ESPECIFICAR]` - Detalhes específicos de implementação
- `[MODIFICAÇÕES]` - Modificações necessárias
- `[TASK_X]` - Tasks específicas do plano de implementação
- `[RESPONSÁVEL]` - Pessoa responsável pela task
- `[DEADLINE]` - Prazo da task

### 4. Checklist de Preenchimento

Antes de finalizar o PRP, verifique se:

- [ ] Todos os placeholders foram substituídos
- [ ] Checkboxes de tipo e prioridade foram marcados
- [ ] Requisitos funcionais estão bem definidos
- [ ] Critérios de aceitação são mensuráveis
- [ ] Componentes afetados estão identificados
- [ ] Plano de implementação está detalhado
- [ ] Riscos foram identificados
- [ ] Definition of Done está completa

## 📋 Templates Disponíveis

### PRP_ISSUE_TEMPLATE.md
Template completo para issues que herda todos os requisitos do `PRP_TEMPLATE_BASE.md`, incluindo:

- ✅ Arquitetura Django + LangChain + Jobs
- ✅ Padrões de Service Layer
- ✅ Repository Pattern
- ✅ Estratégia de testes (AAA pattern)
- ✅ Configurações de segurança
- ✅ Monitoramento e logging
- ✅ Deployment considerations

### Seções Principais

1. **Informações da Issue** - Metadados e classificação
2. **Descrição Detalhada** - Contexto, problema e solução
3. **Requisitos Funcionais e Não Funcionais** - Especificações técnicas
4. **Arquitetura e Design** - Impacto na arquitetura existente
5. **Integrações** - LangChain, Jobs, APIs, Database
6. **Estratégia de Testes** - Cobertura e tipos de teste
7. **Considerações de Segurança** - Aspectos de segurança
8. **Plano de Implementação** - Fases e tasks
9. **Riscos e Mitigações** - Análise de riscos
10. **Definition of Done** - Critérios de finalização

## 🔍 Exemplos de Issues

### Issue de Feature
```
docs/issues/nfe_integration/
├── prp.md                     # PRP completo da feature
├── assets/
│   ├── api_flow_diagram.png   # Diagrama do fluxo da API
│   └── data_model.png         # Modelo de dados
├── research/
│   ├── api_analysis.md        # Análise da API da Fazenda
│   └── security_review.md     # Revisão de segurança
└── decisions/
    └── encryption_method.md   # Decisão sobre criptografia
```

### Issue de Bug Fix
```
docs/issues/job_scheduler_memory_leak/
├── prp.md                     # PRP do bug fix
├── assets/
│   ├── memory_profile.png     # Profile de memória
│   └── error_logs.txt         # Logs do erro
├── research/
│   ├── root_cause_analysis.md # Análise da causa raiz
│   └── performance_tests.md   # Testes de performance
└── decisions/
    └── solution_approach.md   # Abordagem da solução
```

## 📊 Status da Issue

Use os seguintes status no cabeçalho do PRP:

- 🟡 **Draft** - Em elaboração
- 🔄 **In Review** - Em revisão
- ✅ **Approved** - Aprovado para implementação
- 🚀 **In Progress** - Em desenvolvimento
- ✅ **Done** - Concluído

## 🤝 Processo de Aprovação

1. **Draft** - Autor cria o PRP inicial
2. **Tech Review** - Revisão técnica pela equipe
3. **Stakeholder Review** - Revisão por stakeholders
4. **Final Approval** - Aprovação final para desenvolvimento
5. **Implementation** - Desenvolvimento da solução
6. **Done** - Issue finalizada e documentada

## 📚 Referências

- [PRP_TEMPLATE_BASE.md](../PRP_TEMPLATE_BASE.md) - Template base do projeto
- [Django Best Practices](https://django-best-practices.readthedocs.io/)
- [LangChain Documentation](https://python.langchain.com/)
- [Clean Architecture](https://github.com/cosmicpython/book)

## 💡 Dicas

### Para Autores
- Seja específico nos requisitos e critérios de aceitação
- Inclua diagramas e fluxos quando necessário
- Considere impactos na arquitetura existente
- Documente decisões técnicas importantes

### Para Revisores
- Verifique alinhamento com arquitetura do projeto
- Valide critérios de aceitação mensuráveis
- Confirme cobertura de testes adequada
- Avalie riscos e mitigações propostas

### Para Desenvolvedores
- Use o PRP como guia durante desenvolvimento
- Mantenha o documento atualizado com mudanças
- Documente decisões tomadas durante implementação
- Valide Definition of Done antes de finalizar

---

*Este README deve ser atualizado sempre que novos padrões ou templates forem adicionados.*
