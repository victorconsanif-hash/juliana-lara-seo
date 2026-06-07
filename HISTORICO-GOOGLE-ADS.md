# Histórico de Otimizações — Advogada Juliana Lara

**Customer ID:** 2236922800
**Conta:** Advogada Juliana Lara (Direito do Consumidor + Direito de Família, Sorocaba/SP)

> **⚠️ Este arquivo está espelhado em 2 locais — mantenha AMBOS sincronizados:**
> 1. `~/.claude/skills/google-ads-ratos/historico/juliana-lara.md` (canonical, skill, universal)
> 2. `<projeto-juliana>/HISTORICO-GOOGLE-ADS.md` (cópia no projeto pra acesso fácil)
>
> Quando atualizar, o Claude deve gravar nos DOIS arquivos. Conteúdo idêntico nos dois.
>
> Este arquivo é a memória persistente das otimizações desta conta. O Claude DEVE ler antes
> de propor qualquer mudança. Cada sessão de revisão adiciona nova seção no topo.

---

## 🗓️ 2026-05-10 (parte 4) — Migração de domínio: apex → site SEO

**Contexto:** com a integração da parte 3 validada end-to-end, migramos o domínio principal `advogadajulianalara.com.br` para servir o site SEO (Vercel) no lugar do WordPress que estava no apex (Hostinger).

### Estado anterior
- `advogadajulianalara.com.br` (apex) → A `89.116.115.37` (Hostinger / WordPress)
- `www.advogadajulianalara.com.br` → A `89.116.115.37` via CNAME → apex (Hostinger / WordPress)
- `lp.advogadajulianalara.com.br` → A `76.76.21.142` (Vercel / projeto LP)
- DNS gerenciada em Hostinger (NS `ns1/ns2.dns-parking.com`)

### Mudanças aplicadas

**No Vercel** (projeto `juliana-lara-seo`, id `prj_qc0ZlA152YlYH85JVhrTZzhxG5Uy`):
- Apex `advogadajulianalara.com.br` adicionado como Production (sem redirect).
- `www.advogadajulianalara.com.br` adicionado com redirect 307 → apex (Vercel não ofereceu 308 nesse plano).
- `juliana-lara-seo.vercel.app` mantido.

**Na Hostinger** (DNS):
- A `@` alterado de `89.116.115.37` para `216.198.79.1` (Vercel novo IP, com IP-range expansion).
- AAAA `@` (IPv6 `2a02:4780:13:1410:0:39a7:baec:2`) removido — estava conflitando.
- CNAME `www` alterado de `advogadajulianalara.com.br` para `bcaf24dee3aca950.vercel-dns-017.com.` (endpoint dedicado do Vercel pro projeto).
- TXT/MX/NS preservados (e-mail Hostinger continua funcionando).

**No git/Vercel:**
- Commit `09c1a04` (integração SEO → n8n → Agendor) pushed pra `origin/main`.
- Vercel buildou como Preview e foi promovido manualmente pra Production (deploy id `dpl_3GpAUYHRKaoVNiZJAfMY6pX6TS9C`). **Investigar:** auto-promote pra Production está desabilitado nesse projeto — checar Settings → Git → Production Branch.

### Validação final ✅
- `https://advogadajulianalara.com.br/` — 200, SSL OK, integração captureUtms presente.
- `https://advogadajulianalara.com.br/divorcio-sorocaba` — 200, `lpOrigem="seo-divorcio-sorocaba"`, webhook `seo-juliana-agendor` no HTML.
- `https://www.advogadajulianalara.com.br/` — 307 → apex (funcional, mas idealmente 308).
- Custom fields novos `motivo` e `conversion_url` criados no Agendor pela usuária e populando.
- Lead de teste real (`TESTE custom fields`) criado e validado com 11 campos preenchidos, depois deletado via API.

### Pegadinhas técnicas registradas

**Cache stale do Vercel após mudança DNS:** mesmo após remover o AAAA na Hostinger e Google/Cloudflare DoH confirmarem ausência, Vercel continuou mostrando "Invalid Configuration" no apex citando o AAAA antigo. Refresh múltiplos não resolveram. Solução que funcionou: remover o domínio do projeto Vercel e re-adicionar — bypass do cache do resolver interno deles.

**Cert SAN insuficiente após adicionar www:** depois de adicionar `www`, o cert do Vercel ficou só com `CN=www.advogadajulianalara.com.br` e o apex passou a falhar SSL (`subjectAltName does not match`). O remove+re-add do apex força reemissão com ambos os domínios no SAN.

**Direção do redirect www↔apex:** o checkbox "(Recommended)" do Vercel propõe `apex → www`, mas como o canonical do `Layout.astro` aponta pro apex (`https://advogadajulianalara.com.br/`), invertemos pra `www → apex` (radio "Redirect to Another Domain").

**Localhost interceptação:** durante teste local com `npm run dev`, browser hitando `localhost:4321` no Windows pegava outro processo Windows-side (curso-cadeira) ao invés do WSL2. Solução: rodar com `--host` e usar IP da rede do WSL (`http://172.17.5.135:4321/`).

### Pendências
- 🔍 **WordPress órfão na Hostinger:** o conteúdo do WP não foi apagado, só o domínio que apontava pra ele saiu. Se precisar de algum conteúdo dele, está no painel Hostinger. Caso contrário, pode ser desativado quando ela quiser.
- 🔍 **Auto-promote Production no Vercel SEO:** investigar por que `git push` não vira deploy de produção automaticamente (último commit antes da migração também tinha ficado só Preview).
- 🔍 **Atualizar redirect www → apex pra 308** quando Vercel oferecer (atualmente 307 funciona).
- 🔍 **LP em `lp.advogadajulianalara.com.br`** continua ativa. Decidir se desativa ou se mantém pra Ads enviarem tráfego pra LP separada (recomendado manter, é mais rápido pra ROI de Ads que SEO indexar páginas novas).

---

## 🗓️ 2026-05-10 (parte 3) — Integração site SEO → n8n → Agendor

**Contexto:** após a integração da LP (parte 2), portamos o mesmo pipeline pro site SEO `juliana-lara-seo` (Astro, hoje em `juliana-lara-seo.vercel.app`, será promovido pra `https://advogadajulianalara.com.br/` substituindo a LP atual nesse domínio). Antes, os formulários do site SEO faziam POST num webhook simples (`d7fa528e-...`) sem capturar UTMs e sem integração com Agendor.

### O que foi feito

**1. Captura UTM no site SEO (`src/scripts/utm.ts`)**
- Mesmo arquivo da LP, copiado literal. Cookie `juli_utm` (30d, first-touch), 7 UTMs + `page_url` + `first_seen_at`.
- `Layout.astro` chama `captureUtms()` e expõe `getUtms` em `window`. GTM `GTM-MH78G7P9` mantido (mesmo da LP) e marcado `is:inline`.

**2. Workflow n8n novo: "SEO Juliana → Agendor"** (id `QilTCjYSaz0DxAHv`)
Clonado do workflow da LP (`arEkd9uafweHY28q`) via API. Mesma estrutura de 4 nodes (Webhook → Format WhatsApp → Criar Pessoa → Criar Deal). Diferenças vs LP:
- **Webhook path:** `seo-juliana-agendor` (URL produção `https://n8n-n8n-start.p5vluh.easypanel.host/webhook/seo-juliana-agendor`).
- **2 custom fields novos no body do "Criar Deal":** `motivo` (vem do select do FormContato) e `conversion_url` (URL onde o lead converteu, distinta de `page_url` que é a primeira visita do cookie).
- **Reaproveita** os 9 custom fields da LP no Agendor (utm_source...page_url, IDs 49979–49987) e a credencial `qgcnF40NJiBrkOKj` (Agendor API).

**Pegadinha encontrada:** ao clonar via API, removi o `webhookId` (achando que evitava conflito) — n8n não regenera sozinho e o webhook respondeu 404 mesmo com workflow ativo. Fix: gerar UUID novo, escrever no node Webhook via PUT, deactivate+activate. Anotado em "Aprendizados técnicos" abaixo.

**3. Componentes de form do SEO atualizados**
- `src/components/FormContato.astro` e `FormContatoSimples.astro` agora aceitam prop `lpOrigem` (obrigatória), apontam pro novo webhook, e enviam payload completo `{ nome, whatsapp, motivo, lp_origem, conversion_url, ...utms }`.
- IDs internos dos forms agora são namespaced por instância (random uid no SSR) — corrigiu bug pré-existente onde `<FormContato />` usado 2× na mesma page tinha IDs duplicados e o segundo botão não submetia.

**4. Pages do SEO passando lpOrigem por página**
| Page | lpOrigem |
|---|---|
| `index.astro` | `seo-home` |
| `divorcio-sorocaba.astro` | `seo-divorcio-sorocaba` |
| `guarda-filhos-sorocaba.astro` | `seo-guarda-filhos-sorocaba` |
| `pensao-alimenticia-sorocaba.astro` | `seo-pensao-alimenticia-sorocaba` |
| `inventario-sorocaba.astro` | `seo-inventario-sorocaba` |
| `golpe-pix-sorocaba.astro` | `seo-golpe-pix-sorocaba` |
| `nome-negativado-sorocaba.astro` | `seo-nome-negativado-sorocaba` |
| `plano-de-saude-sorocaba.astro` | `seo-plano-de-saude-sorocaba` |
| `blog/[slug].astro` | `blog-{post.id}` (dinâmico) |

**5. Página `obrigado.astro`** — adicionado `dataLayer.push({event:'conversao_formulario', pagina:'obrigado'})` igual à LP, pra event de conversão GTM funcionar.

### Validação end-to-end ✅

Lead real criado durante teste em `localhost:4321` (via WSL `--host`):
- "Victor teste" (FormContatoSimples na home) → deal "Victor teste - seo-home" no Agendor, `lp_origem: seo-home`, `page_url: http://172.17.5.135:4321/`.
- "Victor teste 2" (FormContato em `/guarda-filhos-sorocaba`) → deal "Victor teste 2 - seo-guarda-filhos-sorocaba", `lp_origem: seo-guarda-filhos-sorocaba`, `page_url` mantido como home (cookie first-touch funcionando).
- UTMs vazios (acesso direto, esperado).
- `motivo` e `conversion_url` enviados no payload, mas **não persistem no Agendor** porque os custom fields ainda não existem lá (API só lê definitions, criar é manual).
- Ambos leads de teste foram limpos após validação (DELETE /v3/people/{id} via API).

### Pendência manual no Agendor

🔍 **Criar 2 custom fields novos** em escopo de Negócio (Deal), tipo Texto:
- `motivo`
- `conversion_url`

Sem isso, o pipeline funciona mas esses 2 campos ficam invisíveis no Agendor. Os 9 da LP (utm_source...page_url, lp_origem) já estão preenchendo normalmente.

### Pendências futuras / observar

🔍 **Deploy + DNS:** trocar destino do `advogadajulianalara.com.br` no Vercel — sair da LP atual, apontar pro deploy do `juliana-lara-seo`. `astro.config.mjs` já tem `site:` correto e `Layout.astro` gera canonical alinhado.

🔍 **Limpeza de webhook antigo do SEO:** o webhook `d7fa528e-07be-4805-9d32-efdb600f1064` (que os forms apontavam antes) pode ser removido ou desabilitado no n8n quando confirmar o novo em produção.

### Aprendizados técnicos novos

**API n8n — clonar workflow corretamente:**
- Ao copiar nodes pra criar workflow novo, remover `id` interno OK, mas **NÃO remover `webhookId`** sem regenerar — webhook não fica registrado mesmo com workflow ativo. Solução: gerar `uuid.uuid4()` novo e atribuir ao node Webhook antes do POST/PUT.
- Sequência segura: POST `/workflows` → PUT `/workflows/{id}` (com webhookId UUID) → POST `/workflows/{id}/activate`. Ou já criar com webhookId no POST inicial.

**Astro `<script define:vars>`:**
- Pra ter forms reutilizáveis com IDs únicos por instância, gerar `uid` no frontmatter (`Math.random().toString(36).slice(2,10)`) e injetar via `<script define:vars={{uid}}>`. Substitui `is:inline` quando precisa passar valores SSR pro JS.

### Arquivos no repo `juliana-lara-seo`
- `src/scripts/utm.ts` (novo)
- `src/layouts/Layout.astro` (modificado — captureUtms + GTM is:inline)
- `src/components/FormContato.astro` (modificado — prop lpOrigem, webhook novo, UIDs únicos, payload com UTMs)
- `src/components/FormContatoSimples.astro` (modificado — idem)
- `src/pages/index.astro` (modificado — passa lpOrigem="seo-home")
- `src/pages/{divorcio,guarda-filhos,pensao-alimenticia,inventario,golpe-pix,nome-negativado,plano-de-saude}-sorocaba.astro` (7 modificados — passam lpOrigem)
- `src/pages/blog/[slug].astro` (modificado — passa lpOrigem dinâmico)
- `src/pages/obrigado.astro` (modificado — dataLayer.push)
- `scripts/setup_n8n_workflow.py` (novo — clona+ativa workflow)

---

## 🗓️ 2026-05-10 (parte 2) — Integração LP → n8n → Agendor

**Contexto:** após a sessão de otimização do Google Ads, abrimos uma frente nova — fechar o ciclo de medição. Hoje a gente otimiza pelo proxy "conversão" (clique no botão WhatsApp). Com Agendor plugado, podemos otimizar pelo resultado real (lead qualificado, proposta enviada, caso fechado, ROAS).

### Descoberta crítica
**As LPs NÃO tinham backend.** Forms só abriam `wa.me` e os dados nunca eram salvos. Juliana recebia WhatsApp e tinha que criar lead manualmente no Agendor — provavelmente perdendo leads.

### O que foi feito

**1. Captura UTM nas LPs (`src/scripts/utm.ts`)**
- Captura `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `gclid`, `fbclid`, `page_url`, `first_seen_at` da URL na primeira visita
- Persiste em cookie `juli_utm` por 30 dias (first-touch attribution — não sobrescreve em visitas subsequentes)
- Função `getUtms()` exposta em `window` pelo Layout.astro

**2. 9 campos personalizados criados no Agendor** (escopo: deal/negócio, todos tipo Texto)
| Nome | ID Agendor |
|---|---|
| `utm_source` | 49979 |
| `utm_medium` | 49980 |
| `utm_campaign` | 49981 |
| `utm_term` | 49982 |
| `utm_content` | 49983 |
| `gclid` | 49984 |
| `fbclid` | 49985 |
| `lp_origem` | 49986 |
| `page_url` | 49987 |

**Importante:** API do Agendor v3 só permite **ler** custom fields, não criar — tem que criar manualmente no painel.

**3. Workflow n8n novo: "LP Juliana → Agendor"** (id `arEkd9uafweHY28q`)
Criado via API n8n (POST /api/v1/workflows). Estrutura:
```
Webhook → Format WhatsApp (Set) → Criar Pessoa (HTTP) → Criar Deal (HTTP)
```
- **Webhook URL produção:** `https://n8n-n8n-start.p5vluh.easypanel.host/webhook/lp-juliana-agendor`
- Auth Agendor: credential `qgcnF40NJiBrkOKj` (httpHeaderAuth, "Agendor API") — reaproveitada de workflow antigo
- Endpoint pessoa: `POST https://api.agendor.com.br/v3/people`
- Endpoint deal: `POST /v3/people/{id}/deals` com `dealStage: 3668369` (Contato) e `customFields: {...}`
- Title do deal: `{nome} - {lp_origem}`

**4. LPs apontando pro novo webhook**
- `src/pages/consumidor.astro` — lp_origem: "consumidor"
- `src/pages/familia.astro` — lp_origem: "familia"
- Helper `enviarLead(nome, whats)` lê UTMs do cookie e envia payload completo
- Fluxo preservado: abre WhatsApp → POST webhook → redirect `/obrigado`

### Validação end-to-end
Lead real criado no Agendor durante teste:
- Pessoa "victor" (WhatsApp `+5511999999999` formatado)
- Deal "victor - consumidor" no funil "Funil de Vendas", etapa "Contato"
- Custom fields populados: `utm_source: google`, `utm_campaign: teste`, `gclid: ABC123`, `lp_origem: consumidor`, etc.

### Aprendizados técnicos importantes

**API Agendor:**
- Custom fields no body: `{ "customFields": { "utm_source": "google", ... } }` (chave = NAME do campo, não ID)
- Custom fields **não retornam por padrão** no GET — precisa `?withCustomFields=true`
- Auth: `Authorization: Token <api_token>` (não Bearer)
- API só **lê** custom field definitions, não cria

**API n8n:**
- Auth: `X-N8N-API-KEY: <jwt>`
- POST `/api/v1/workflows` aceita: `name`, `nodes`, `connections`, `settings`
- PUT só aceita esses 4 campos — qualquer outro retorna 400 "additional properties"
- POST `/api/v1/workflows/{id}/activate` pra ativar
- Webhook URL é `/webhook/<path>` (campo `path` do node), não `/webhook/<webhookId>`

**Bug pego durante validação:**
- Agendor envelopa todas as respostas em `{ "data": {...} }`. No node de criar deal eu escrevi `$json.id` — dava 405 porque virava `/v3/people//deals` (slash duplo). Corrigir pra `$('Criar Pessoa (Agendor)').item.json.data.id`.

### Workflows n8n antigos (pendência de limpeza)
Arquivar/desativar quando confirmar que tudo está estável:
- "Ads Juliana" (`E8IK-jT__OmlyrZvh-spM`)
- "Ads Juliana - Direito do consumidor" (`0OFUfOKS2DQLvQX4`)
- "Ads Juliana - Novas LPs" (`PVEzWdOHzyocwjJe`)
- "My woLP Juliana → Agendorrkflow 3" (`kph2f11jC0NOOZE_SSvaC`) — vazio
- "Webhook_agendor_Juliana" (`2BXroLU70qxARYs1LV7Gq`)

### Dados de teste no Agendor — ✅ limpeza feita pelo usuário (2026-05-10)
~~Pessoa "TESTE Claude End-to-End" (id 68584443)~~
~~Pessoa "TESTE Claude V2" (id 68584448) + deal id 42143845~~
~~Pessoa "victor" + deal id 42143851 (teste real)~~

### Pendências futuras / observar

🔍 **Deploy:** usuário vai dar `git push` no repo `juliana-lara-lps` — Vercel deploya automaticamente. Confirmar que LP em produção (`lp.advogadajulianalara.com.br`) está funcional.

🔍 **Loss reasons no Agendor:** ainda não cadastradas. Sem isso, ROAS por motivo de perda não é possível. Próxima sessão pedir a lista pra cadastrar.

🔍 **Skill `agendor-ratos`:** próximo passo natural. Mesmo padrão da `google-ads-ratos`, com scripts pra:
- Listar deals com filtros (won/lost, por período)
- Cruzar gclid de Agendor com cliques de Google Ads → ROAS real
- Identificar campanhas que trazem leads de alto valor vs spam

🔍 **Disciplina de uso do CRM:** Juliana precisa registrar valor da proposta + motivo de perda em cada deal. Sem isso, todo o esforço de atribuição vira lixo. Vale alinhar com ela na próxima reunião.

### Arquivos no repo `juliana-lara-lps`
- `src/scripts/utm.ts` (novo)
- `src/layouts/Layout.astro` (modificado — chama captureUtms, expõe getUtms em window, GTM com is:inline)
- `src/pages/consumidor.astro` (modificado — webhook URL nova + UTMs no payload)
- `src/pages/familia.astro` (modificado — idem)
- `scripts/create_n8n_workflow.py` (novo — cria o workflow)
- `scripts/update_n8n_workflow.py` (novo — atualiza workflow corrigindo URL)
- `.env` (novo, gitignored — `AGENDOR_TOKEN`, `N8N_API_KEY`, `N8N_BASE_URL`)

---

## 📋 Estado atual das campanhas (2026-05-10)

| ID | Nome | Status | Budget | CPA atual |
|---|---|---|---|---|
| 23168073581 | Campanha da Conversão | ENABLED | R$ 40/dia | R$ 17,21 (30d) |
| 23730199863 | Direito do Consumidor | ENABLED | R$ 15/dia | R$ 44,76 (30d) |
| 23735956541 | Direito de Família | PAUSED | R$ 15/dia | — |

**Restrição de orçamento:** Cliente quer manter R$ 300 semanais por campanha. **NÃO mexer em budget sem nova autorização.**

**Desktop bid:** -100% (manual, feito pelo usuário em 2026-05-10).

**Sunday schedule:** Pausado pela cliente em 2026-05-10 (estava ativo 16h-22h, 0 conversões em 30d).

---

## 🗓️ 2026-05-10 — Primeira sessão de otimização

### Diagnóstico inicial (últimos 7 dias)
- Conta: 49 cliques, 13 conversões, R$ 267,65 — CPA R$ 20,59
- Campanha da Conversão: CPA R$ 14,61 ⭐ (estrela)
- Direito do Consumidor: CPA R$ 92,27 ⚠️ (problema)
- Impression Share da conta: 9,99% (muito espaço pra escalar)

### Ações aplicadas

**Campanha "Direito do Consumidor" (23730199863):**
- ✅ 6 negativas adicionadas (PHRASE): `como fazer`, `o que fazer`, `como denunciar`, `dicas`, `passo a passo`, `tutorial` — filtra buscas informacionais
- ✅ Keyword pausada: `fui vítima de golpe` (PHRASE) — gastava R$ 35/sem com 0 conv
- ✅ Ad group pausado: **Negativação Indevida** (ID 194842447563) — 1 clique, 0 conv em 30d

**Campanha "Conversão" (23168073581):**
- ✅ Keyword pausada: `advogada de familia` (BROAD, QS=1) no ad group "Dir Familia e Consumidor" — gastou R$ 21 sem converter
- ✅ Ad group reativado: **Dir Familia e Consumidor** (ID 193033556131) — estava PAUSED mas tem 9 conversões em 30d
- ✅ Nova RSA criada (PAUSED, ID 808344845167) no ad group "Direito do Consumidor" (197800328324) — 15 headlines focadas em "advogado direito do consumidor" pra subir QS=5
- ✅ Desktop -100% (manual no painel)
- ✅ Domingo schedule pausado (manual no painel)

**Otimização de horários (Mon-Fri):**
- ✅ Removidos os 5 schedules antigos (Mon-Fri 7h-22h)
- ✅ 30 schedules novos com bid modifiers (6 por dia útil):
  - 7h-8h: default
  - **8h-9h: +20%** ⭐ (CPA R$ 13,70 — hot)
  - 9h-15h: default
  - **15h-16h: +20%** ⭐ (CPA R$ 12,73 — hot)
  - 16h-19h: default (17h hot ficou aqui, sem boost — limite de 6/dia)
  - **19h-21h: +20%** ⭐ (CPA R$ 10,31 e R$ 14,78 — hot)
  - **21h removido** (R$ 93 desperdiçados em 90d, 0 conv)

### Análise de 90 dias (referência)

**Campanha da Conversão — 149 conv em R$ 2.626 — CPA médio R$ 17,62**

Top hours por CPA:
1. 19h: R$ 10,31 / 42,9% tx conv
2. 15h: R$ 12,73 / 29,5%
3. 08h: R$ 13,70 / 31,4%
4. 17h: R$ 13,92 / 27,8% (não recebeu boost por limite)
5. 10h: R$ 14,10 / 25,4% (volume alto)

Top dias da semana:
- Terça: CPA R$ 10,90 🥇
- Sexta: CPA R$ 13,38
- Quarta: CPA R$ 14,75

Pior:
- Segunda: CPA R$ 66,90 (só 1 conv)
- Domingo: 0 conv (pausado)

### Surpresas / aprendizados desta sessão
- **Dados de 7 dias enganaram:** "Cartão e Consignado" parecia perdedor em 7d, mas em 30d é o **melhor** ad group de Direito do Consumidor (CPA R$ 13,92). Sempre cruzar 7d com 30d antes de pausar low-volume ad groups.
- **14h era top em 7d/30d, mediano em 90d.** Janela importa pra hot zones.
- **Ad group "Dir Familia e Consumidor" tava PAUSED por engano** — tem 9 conversões/30d. Reativar foi vitória fácil.
- **Sitelinks "duplicados" eram falso positivo.** A função `extensions` lista todos os assets do MCC; os 4 "Cartão Clonado" eram 4 assets diferentes mas só 1 estava linkado a campanha. Não tem dedup necessário.

### Pendências futuras / observar
- 🔍 **17h sem boost** — perdeu vaga por limite de 6/dia. Reavaliar se outro range pode ceder o slot.
- 🔍 **RSA nova ainda PAUSED** — usuário precisa revisar e ativar (ID 808344845167).
- 🔍 **Direito do Consumidor com poucos dados** — só 69 cliques em 90d. Não tomar grandes decisões até acumular volume.
- 🔍 **16h tem CPA R$ 34,27** mas tem volume (63 cliques, 7 conv em 90d). Não pausar mas considerar -30% bid no futuro.
- 🔍 **Direito de Família** está PAUSED (campanha 23735956541) — tem 5 conv e CPA R$ 42 historicamente. Reativar?

### Skill estendida nesta sessão
Adicionados 4 subcomandos nos scripts (`~/.claude/skills/google-ads-ratos/scripts/`):
- `update.py device-bid` — bid modifier por dispositivo
- `update.py schedule-bid` — bid modifier por dia+hora (limite: 6/dia, sem sobreposição)
- `read.py campaign-assets` — lista asset linkages com resource_name pra delete
- `delete.py campaign-asset` — desvincula asset de campanha (pra dedup de sitelinks)

Aprendizados técnicos salvos em `~/.claude/skills/google-ads-ratos/aprendizados.md`.

---

## 🔁 Processo de revisão semanal (todo domingo)

Próxima revisão sugerida: **2026-05-17 (domingo)**

Quando o usuário disser "revisar campanhas da Juliana" ou for domingo, o Claude deve:

1. **Ler este arquivo** (especialmente "Pendências futuras / observar")
2. **Puxar dados frescos:**
   - `insights.py campaign --customer-id 2236922800 --date-range LAST_7_DAYS`
   - Comparar com semana anterior (registrada aqui)
3. **Verificar pendências da última sessão** — checar se foram resolvidas
4. **Identificar novidades:**
   - Mudança brusca em CPA (>30% pior ou melhor)?
   - Search terms novos relevantes pra negativar?
   - Hot zones de horário mudaram?
5. **Propor 3-5 ações concretas** (não mais que isso)
6. **Após executar, ADICIONAR nova seção neste arquivo** no topo (acima desta)

### Métricas pra acompanhar semanalmente
- CPA por campanha (Conversão / Direito do Consumidor)
- Conversões por dia da semana
- Top search terms novos
- Quality Score das keywords principais
- Impression Share

---
