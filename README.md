# 🎬 WhatsCompress V4.0

**Compressor de vídeos para WhatsApp — Windows 10/11 (64 bits), saída MP4 e uso portátil.**

O WhatsCompress foi pensado para ser simples: **arraste ou selecione o vídeo**, escolha um tamanho máximo e clique em **COMPRIMIR**. O resultado fica junto ao arquivo original, com o sufixo **`(WHATSAPP)`**.

> **Download oficial:** [WhatsCompress v4.0 — Windows portátil](https://github.com/UNREALWINS/whatscompress/releases/tag/v4.0). O aplicativo é fornecido como ZIP com o executável e suas dependências. A compilação automatizada e os testes passaram; recomenda-se validar o uso no seu Windows.

## Recursos

- Interface gráfica **horizontal**, letras grandes e áreas roláveis para notebooks menores.
- Adição de vários arquivos por **arrastar e soltar** ou clique na área de seleção.
- Quatro tamanhos máximos por vídeo: **30 MB, 64 MB, 100 MB e 150 MB** (MB decimal = 1.000.000 bytes).
- Saída **`.mp4`**, vídeo H.264 e áudio AAC quando há recodificação.
- **Modo Rápido:** uma passagem, com tentativa de aceleração por GPU NVIDIA/Intel/AMD; alternativa por CPU.
- **Modo Preciso:** codificação x264 em duas passagens. O modo Rápido pode recorrer a duas passagens se passar do limite.
- Barras de progresso do arquivo atual e do lote; botão de cancelamento.
- O vídeo original é preservado. Saída ao lado dele: `Vídeo 03 (WHATSAPP).mp4`.
- Ao concluir, pode abrir o Explorador de Arquivos com o MP4 selecionado.
- Se o MP4 original já for compatível e estiver abaixo do limite, copia sem recomprimir.
- Verifica se **`bin/ffmpeg.exe`** e **`bin/ffprobe.exe`** já funcionam antes de baixá-los.

**Importante:** o limite selecionado é um *máximo*, não um tamanho exato. A velocidade e a qualidade dependem da duração, resolução e hardware; codificação precisa pode demorar mais.

## Baixar o aplicativo pronto (recomendado)

1. Abra [Releases — WhatsCompress v4.0](https://github.com/UNREALWINS/whatscompress/releases/tag/v4.0).
2. Em **Assets / Arquivos**, baixe `WhatsCompress_V4_PORTABLE_WINDOWS.zip`.
3. Extraia toda a pasta `WhatsCompress` e abra `WhatsCompress.exe`.
4. Não é preciso instalar Python, PySide6 ou FFmpeg. Mantenha as pastas `_internal` e `bin` junto do executável.

> O ZIP disponível em **Code → Download ZIP** contém **apenas o código-fonte**; para usar o aplicativo sem instalar dependências, baixe a versão em **Releases**.

## Para usar o projeto no Windows

1. Baixe o código em **Code → Download ZIP** e extraia em uma pasta.
2. Execute **`BAIXAR_FFMPEG.bat`** (se ambos os arquivos já funcionarem em `bin`, não haverá novo download).
3. Execute **`INICIAR_TESTE.bat`** para abrir a interface. Nesta etapa, **Python** e PySide6 são usados no computador de desenvolvimento.
4. Adicione os arquivos, selecione 30/64/100/150 MB e clique em **COMPRIMIR**.

### Como gerar o aplicativo portátil

Com o FFmpeg pronto, execute **`INSTALAR_E_GERAR_EXE.bat`** no computador de desenvolvimento. O script instala PySide6/PyInstaller, compila e cria **`WhatsCompress_V4_PORTABLE_WINDOWS.zip`**. No outro computador, basta extrair a pasta e abrir **`WhatsCompress.exe`**; **não é necessário instalar Python**.

**Não copie apenas o `.exe`:** preserve a estrutura `WhatsCompress/`, inclusive `_internal/` e `bin/`.

## Gerar o portátil pelo GitHub Actions

É possível gerar o ZIP para Windows **sem configurar Python no seu computador**:

1. Abra a guia **Actions (Ações)** e escolha **Gerar aplicativo portátil para Windows**.
2. O processo é iniciado automaticamente a cada envio de código para `main`. Também pode ser iniciado pelo botão **Run workflow (Executar fluxo de trabalho)**.
3. Quando terminar, abra a execução e baixe o artefato **`WhatsCompress-V4-Windows-Portable`**.
4. Extraia o ZIP do artefato. Nele estará o arquivo **`WhatsCompress_V4_PORTABLE_WINDOWS.zip`** com o aplicativo.

A automação baixa o FFmpeg durante a compilação; **não** armazena binários grandes no repositório. As versões oficiais podem ser obtidas em [Releases](https://github.com/UNREALWINS/whatscompress/releases). A automação também conserva o artefato temporário de compilação. Recomenda-se testar o executável em um PC Windows antes de usá-lo com arquivos importantes.

## Desenvolvimento e testes

- Linguagem: Python 3.10+ (recomendado 3.12/3.14 com pacotes compatíveis)
- Interface: PySide6
- Conversão: FFmpeg / FFprobe
- Empacotamento: PyInstaller (Windows)

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s testes -v
```

Os testes de conversão exigem FFmpeg e FFprobe acessíveis em `bin/` ou no `PATH`.

## Arquivos principais

| Arquivo | Finalidade |
|---|---|
| `whatscompress.py` | Interface gráfica em PySide6 |
| `compressor.py` | Conversão, tamanho, aceleração e nomes de saída |
| `BAIXAR_FFMPEG.bat` | Prepara o FFmpeg caso esteja ausente |
| `scripts_baixar_ffmpeg.ps1` | Download e validação do FFmpeg |
| `INICIAR_TESTE.bat` | Abre a interface em ambiente de desenvolvimento |
| `INSTALAR_E_GERAR_EXE.bat` | Compila o portátil no Windows |
| `testes/` | Testes automatizados |

## Licenças e redistribuição

O repositório **não inclui, por enquanto, uma licença de código aberto** para o código próprio. Antes de reutilizar ou redistribuir o código, é necessário definir a licença com o autor. O aplicativo usa bibliotecas e executáveis de terceiros, como **PySide6, PyInstaller e FFmpeg**, com licenças próprias. Confira as obrigações aplicáveis à versão específica do FFmpeg distribuída no pacote. Veja [AVISOS_TERCEIROS.md](AVISOS_TERCEIROS.md).

---

Feito para simplificar o envio de vídeos pelo WhatsApp. Este projeto **não é afiliado ao WhatsApp ou à Meta**.