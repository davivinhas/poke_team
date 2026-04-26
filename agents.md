# agents.md

## Visao do dominio

Esta aplicacao modela a montagem e gestao de times Pokemon.
O foco do dominio e permitir que um usuario monte times com ate 6 Pokemon, cada Pokemon do time com seus IVs e ate 4 movimentos, usando dados oficiais da PokeAPI como fonte externa de referencia.

## Objetivo principal

- Permitir criar, consultar, editar e remover times de Pokemon por usuario.
- Tratar `PokemonSpecie` e `Movement` como catalogos de referencia do jogo.
- Popular `PokemonSpecie` e `Movement` sob demanda (lazy load), consultando a PokeAPI quando o dado ainda nao existir localmente.
- Evoluir para suportar `HoldObject` (itens segurados) por Pokemon do time.

## Linguagem ubiqua

- `User`: dono dos times.
- `Team`: agregado raiz com identidade propria e lista de Pokemon do time.
- `TeamPokemon`: instancia de um Pokemon dentro de um time.
- `PokemonSpecie`: especie base (ex.: Pikachu), com tipo(s) e base stats.
- `Movement`: movimento aprendivel por especie (ex.: Thunderbolt).
- `MovementSlot`: associacao de um movimento com a posicao 1..4 no Pokemon do time.
- `IVs`: valores individuais de batalha (0..31).
- `BaseStats`: stats base da especie (1..255).
- `Types`: tipo elemental do Pokemon/movimento.
- `HoldObject` (futuro): item segurado por `TeamPokemon`.

## Regras de negocio atuais (dominio)

- Um `Team` deve ter `id > 0` e `name` nao vazio.
- Um `Team` pode ter no maximo 6 `TeamPokemon`.
- Um `TeamPokemon` deve ter `id > 0`, `specie` valida e `ivs` valido.
- Um `TeamPokemon` pode ter no maximo 4 movimentos.
- Um `PokemonSpecie` deve ter:
  - `id > 0`
  - `external_id > 0` (id da PokeAPI)
  - `name` nao vazio
  - `base_stats` valido
  - entre 1 e 2 tipos
- `BaseStats`: cada stat entre 1 e 255.
- `IVs`: cada stat entre 0 e 31.
- `MovementSlot`: ordem obrigatoria entre 1 e 4 e `movement` valido.

## Modelo de agregados

Agregado principal: `Team`

- Entidades internas do agregado:
  - `TeamPokemon`
- Objetos de valor internos:
  - `IVs`
  - `MovementSlot`

Catalogos externos ao agregado do time (referencia):

- `PokemonSpecie`
- `Movement`

Esses catalogos sao compartilhados por varios times e devem ser tratados como dados de referencia, nao como estado interno do agregado `Team`.

## Integracao com PokeAPI (povoamento sob demanda)

### Estrategia

- **Fonte da verdade externa**: PokeAPI.
- **Fonte da verdade local de leitura/escrita da aplicacao**: banco local.
- Fluxo recomendado para `PokemonSpecie` e `Movement`:
  1. Caso de uso consulta repositorio/gateway local.
  2. Se encontrado localmente, retorna sem chamar API externa.
  3. Se nao encontrado, consulta PokeAPI via gateway de infraestrutura.
  4. Mapeia DTO externo -> entidade de dominio.
  5. Persiste localmente (cache duravel).
  6. Retorna para o caso de uso.

### Beneficios

- Reduz latencia em chamadas repetidas.
- Evita acoplamento do dominio com contrato externo.
- Facilita testes, pois portas permitem mocks/stubs.
- Mantem a aplicacao funcional mesmo com indisponibilidade parcial da API externa (com dados ja cacheados).

## Arquitetura (Hexagonal / Clean)

Camadas propostas, mantendo 99% dos padroes:

- `domain`: entidades, VOs, regras invariantes, sem dependencia de framework.
- `application`: casos de uso e portas (`ports`). Orquestra dominio e gateways.
- `infrastructure`: adaptadores de persistencia e integracao externa (PokeAPI, banco, cache).
- `presentation`: controllers/rotas HTTP (FastAPI), DTOs de entrada/saida.

Dependencias sempre apontam para dentro:

- `presentation` -> `application`
- `infrastructure` -> `application` e `domain`
- `application` -> `domain`
- `domain` -> (nenhuma camada externa)

## Portas atuais identificadas

- `TeamRepositoryPort`
  - salvar, buscar por id, listar por usuario, deletar.
- `PokemonSpeciesGateway`
  - buscar por id e pesquisar por filtros/paginacao por cursor.
- `MovementsGateway`
  - pesquisar movimentos por tipo e/ou especie.

Observacao: para o modo lazy load com PokeAPI, a implementacao de infraestrutura pode usar adaptadores separados para:

- leitura local (repositorio)
- consulta externa (cliente PokeAPI)
- servico de sincronizacao sob demanda (application service)

## Casos de uso esperados

- Criar time para usuario.
- Renomear time.
- Adicionar/remover `TeamPokemon` do time.
- Definir/alterar IVs do Pokemon no time.
- Definir movimentos (slots 1..4) do Pokemon no time.
- Buscar especie por id/nome/tipo com auto-populacao sob demanda.
- Buscar movimentos por tipo/especie com auto-populacao sob demanda.

## Evolucao planejada: HoldObject

Objetivo: cada `TeamPokemon` pode segurar 0 ou 1 item.

Recomendacao de modelagem:

- Nova entidade/VO de catalogo: `HoldObject` (id interno, external_id, name, descricao, efeitos).
- Em `TeamPokemon`: campo opcional `hold_object`.
- Novas regras de dominio:
  - item opcional (pode ser `None`)
  - no maximo 1 item por Pokemon do time
- Porta de aplicacao sugerida:
  - `HoldObjectsGateway` com busca por id/nome e estrategia lazy load igual a species/movements.

## Diretrizes para manter padrao arquitetural

- Nao usar entidades de dominio diretamente como payload HTTP.
- Nao deixar regras de negocio em controller, repository ou cliente externo.
- Tratar PokeAPI como detalhe de infraestrutura.
- Isolar mapeamentos em mappers/assemblers na borda da aplicacao.
- Testar dominio com testes unitarios puros (sem framework/banco).
- Testar casos de uso com portas mockadas.
- Testar adaptadores de infraestrutura com testes de integracao.

## Diretriz de desenvolvimento orientado a testes

Para fins de aprendizado, toda evolucao da aplicacao deve ser acompanhada de testes automatizados.

- Regra pratica: **sem teste novo/ajustado, sem feature pronta**.
- Priorizar TDD sempre que possivel:
  1. escrever primeiro um teste que falha;
  2. implementar o minimo para passar;
  3. refatorar mantendo os testes verdes.
- Cobrir pelo menos:
  - regras de negocio do dominio (casos felizes e invalidos);
  - casos de uso da camada application (com mocks das portas);
  - adaptadores de infraestrutura criticos (integracao).
- Para integracao com PokeAPI, testar os cenarios:
  - dado encontrado localmente (nao chamar API externa);
  - dado nao encontrado localmente (chamar API externa, mapear e persistir);
  - falha externa com dados ja cacheados (degradacao controlada quando aplicavel).

## Resumo operacional

O coracao da aplicacao e o agregado `Team`. `PokemonSpecie` e `Movement` funcionam como catalogos de referencia sincronizados sob demanda com a PokeAPI e persistidos localmente. A proxima extensao natural do dominio e `HoldObject` por `TeamPokemon`, mantendo o mesmo padrao de portas, casos de uso e adaptadores, sem quebrar os principios de Hexagonal/Clean Architecture.
