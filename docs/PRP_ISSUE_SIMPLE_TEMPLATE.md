# PRP (Product Requirement Prompt) - Issue Simples
## Template Simplificado

### Issue ID: [SUBSTITUIR_POR_ID_DA_ISSUE]
### Data: [SUBSTITUIR_POR_DATA]

---

## 📋 Resumo

**Título**: [SUBSTITUIR_POR_TITULO_DA_ISSUE]

**Tipo**: [Bug Fix / New Feature / Enhancement / Other]

---

## 📝 Descrição Detalhada

### Contexto
[DESCREVER_O_CONTEXTO_DA_ISSUE]

### Problema Atual
[DESCREVER_O_PROBLEMA_OU_NECESSIDADE]

### Solução Proposta
[DESCREVER_A_SOLUÇÃO_PROPOSTA]

### Benefícios Esperados
- [BENEFICIO_1]
- [BENEFICIO_2]
- [BENEFICIO_N]

### Por que é importante?
[JUSTIFICATIVA_DA_ISSUE]

### Critérios de Aceitação
- [ ] [CRITERIO_1]
- [ ] [CRITERIO_2]
- [ ] [CRITERIO_3]

---

## 🎯 Requisitos Funcionais

### RF01 - [NOME_DO_REQUISITO]
**Descrição**: [DESCRIÇÃO_DETALHADA]
**Critérios de Aceitação**:
- [ ] [CRITERIO_1]
- [ ] [CRITERIO_2]
- [ ] [CRITERIO_N]

### RF02 - [NOME_DO_REQUISITO]
**Descrição**: [DESCRIÇÃO_DETALHADA]
**Critérios de Aceitação**:
- [ ] [CRITERIO_1]
- [ ] [CRITERIO_2]
- [ ] [CRITERIO_N]

---

## 🔧 Requisitos Não Funcionais

### RNF01 - Performance
**Descrição**: [REQUISITOS_DE_PERFORMANCE]
**Métricas**:
- Tempo de resposta: [TEMPO_ESPERADO]
- Throughput: [THROUGHPUT_ESPERADO]
- Uso de CPU/Memória: [LIMITES]

### RNF02 - Segurança
**Descrição**: [REQUISITOS_DE_SEGURANÇA]
**Controles**:
- [ ] [CONTROLE_1]
- [ ] [CONTROLE_2]
- [ ] [CONTROLE_N]

### RNF03 - Escalabilidade
**Descrição**: [REQUISITOS_DE_ESCALABILIDADE]
**Considerações**:
- [CONSIDERAÇÃO_1]
- [CONSIDERAÇÃO_2]
- [CONSIDERAÇÃO_N]

---

## 🏗️ Arquitetura e Design

### Componentes Afetados
Baseado na arquitetura do [PRP_BASE.md](./PRP_BASE.md):

#### Django Apps
- [ ] `apps.jobs` - [DESCREVER_MODIFICAÇÕES]
- [ ] `apps.langchain_integration` - [DESCREVER_MODIFICAÇÕES]
- [ ] `core` - [DESCREVER_MODIFICAÇÕES]
- [ ] Outras: [ESPECIFICAR]

#### Services
- [ ] `TextProcessorService` - [MODIFICAÇÕES]
- [ ] `JobSchedulerService` - [MODIFICAÇÕES]
- [ ] Novos services: [ESPECIFICAR]

#### Models
- [ ] Novos models: [ESPECIFICAR]
- [ ] Models modificados: [ESPECIFICAR]
- [ ] Migrations necessárias: [ESPECIFICAR]

### Diagrama de Arquitetura
```
[INCLUIR_DIAGRAMA_SE_NECESSÁRIO]
```

### Fluxo de Dados
```
[DESCREVER_FLUXO_DE_DADOS]
1. [PASSO_1]
2. [PASSO_2]
3. [PASSO_N]
```

---

## 🔌 Integrações

### LangChain
- **Chains necessárias**: [ESPECIFICAR]
- **Prompts**: [LISTAR_PROMPTS]
- **Models**: [ESPECIFICAR_MODELOS]
- **Configurações**: [CONFIGURAÇÕES_ESPECÍFICAS]

### Jobs/Schedulers
- **Novos jobs**: [ESPECIFICAR]
- **Jobs modificados**: [ESPECIFICAR]
- **Frequência**: [ESPECIFICAR]
- **Dependências**: [ESPECIFICAR]

### APIs Externas
- **Endpoints**: [LISTAR_ENDPOINTS]
- **Autenticação**: [TIPO_DE_AUTH]
- **Rate Limits**: [ESPECIFICAR_LIMITES]
- **Error Handling**: [ESTRATÉGIAS]

### Base de Dados
- **Tabelas afetadas**: [ESPECIFICAR]
- **Índices necessários**: [ESPECIFICAR]
- **Queries críticas**: [ESPECIFICAR]
- **Backup considerations**: [ESPECIFICAR]

---

### Configurações Necessárias
- [ ] Environment variables: [LISTAR_SE_HOUVER]
- [ ] Database migrations: [SIM/NÃO]
- [ ] New dependencies: [LISTAR_SE_HOUVER]

---

## 🚀 Plano de Implementação

### Fase 1: Preparação
- [ ] [TASK_1] - [RESPONSÁVEL] - [DEADLINE]
- [ ] [TASK_2] - [RESPONSÁVEL] - [DEADLINE]
- [ ] [TASK_N] - [RESPONSÁVEL] - [DEADLINE]

### Fase 2: Implementação Core
- [ ] [TASK_1] - [RESPONSÁVEL] - [DEADLINE]
- [ ] [TASK_2] - [RESPONSÁVEL] - [DEADLINE]
- [ ] [TASK_N] - [RESPONSÁVEL] - [DEADLINE]

### Fase 3: Integração e Testes
- [ ] [TASK_1] - [RESPONSÁVEL] - [DEADLINE]
- [ ] [TASK_2] - [RESPONSÁVEL] - [DEADLINE]
- [ ] [TASK_N] - [RESPONSÁVEL] - [DEADLINE]

### Fase 4: Deploy e Monitoramento
- [ ] [TASK_1] - [RESPONSÁVEL] - [DEADLINE]
- [ ] [TASK_2] - [RESPONSÁVEL] - [DEADLINE]
- [ ] [TASK_N] - [RESPONSÁVEL] - [DEADLINE]

---

## 🧪 Testes

### Testes Necessários
- [ ] Unit tests para [COMPONENTE]
- [ ] Integration tests para [FLUXO]
- [ ] Manual tests para [CENÁRIO]

### Cenários de Teste
1. **Cenário feliz**: [DESCREVER]
2. **Cenários de erro**: [DESCREVER]
3. **Edge cases**: [DESCREVER]

---

## ✅ Definition of Done

- [ ] Código implementado e funcionando
- [ ] Testes unitários passando
- [ ] Funcionalidade validada
- [ ] Documentação atualizada (se necessário)

---

## 📚 Referências

- Requisitos em: [PRP_BASE.md](../PRP_BASE.md)
- Issues relacionadas: [#NUMERO - TÍTULO]
- Documentação: [LINKS_RELEVANTES]

---

**Status**: 🟡 Draft  
**Responsável**: [NOME_DO_RESPONSÁVEL]  
**Data Prevista**: [DATA_DE_CONCLUSÃO]
