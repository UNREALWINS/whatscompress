# WhatsCompress v4.0 — primeira versão oficial 🎬

Aplicativo portátil para **Windows 10/11 (64 bits)** que converte e comprime vídeos para **MP4**, com foco no envio pelo WhatsApp.

## Como instalar e usar

1. Baixe o arquivo **`WhatsCompress_V4_PORTABLE_WINDOWS.zip`** abaixo, em **Assets / Arquivos desta versão**.
2. Extraia **todo o ZIP** em uma pasta do computador.
3. Abra **`WhatsCompress\WhatsCompress.exe`** (mantenha também as pastas `_internal` e `bin`).
4. Arraste um ou mais vídeos para o aplicativo ou clique para selecionar.
5. Escolha o limite de **30, 64, 100 ou 150 MB**, selecione o modo desejado e clique em **COMPRIMIR**.

**Não é necessário instalar Python nem FFmpeg.** O vídeo original permanece intacto.

## Novidades da versão 4.0

- Interface horizontal com fontes maiores para notebooks pequenos.
- Arrastar e soltar, seleção por clique e fila de vídeos.
- Barras de progresso por vídeo e do lote, com cancelamento.
- **Modo Rápido**: tenta aceleração de hardware (NVIDIA, Intel e AMD) e usa CPU como alternativa.
- **Modo Preciso**: codificação em duas passagens para maior controle de tamanho.
- Saída sempre em **MP4**, geralmente H.264 + AAC.
- Grava ao lado do arquivo original, por exemplo **`Vídeo 03 (WHATSAPP).mp4`**.
- Ao concluir, pode abrir a pasta com o vídeo convertido selecionado.

**Observação:** os valores em MB são limites máximos *aproximados*, não tamanhos exatos; o aplicativo procura ficar abaixo do valor escolhido. Velocidade e qualidade dependem do vídeo e do computador.

## Segurança e verificação

O arquivo `SHA256SUMS.txt` contém o resumo SHA-256 do ZIP para conferência da integridade. Este é um executável portátil gerado pelo GitHub Actions; um aviso do Windows SmartScreen pode ocorrer por não haver assinatura digital de código.

## Licenças e créditos

WhatsCompress é um projeto independente, sem afiliação com o WhatsApp ou a Meta. A distribuição inclui componentes de terceiros:
- **FFmpeg/FFprobe (GPLv3 na compilação Gyan)**: https://www.gyan.dev/ffmpeg/builds/ — código-fonte e licenças: https://ffmpeg.org/ e https://github.com/FFmpeg/FFmpeg
- **Qt/PySide6**: https://doc.qt.io/qtforpython-6/licenses.html
- **PyInstaller**: https://pyinstaller.org/en/stable/license.html

Consulte `AVISOS_TERCEIROS.md` incluído no ZIP e no [repositório](https://github.com/UNREALWINS/whatscompress). O código próprio do WhatsCompress ainda não possui licença aberta expressa.

---
**Primeira versão oficial:** compilação Windows automatizada e testes de conversão; recomenda-se testar em seu computador antes de utilizar vídeos importantes.
