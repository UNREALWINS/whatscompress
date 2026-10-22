# Avisos e licenças de componentes de terceiros

Este projeto usa programas e bibliotecas de terceiros, que **não são de autoria do WhatsCompress**. O código-fonte próprio encontra-se neste repositório e, por enquanto, **não possui licença aberta expressa**.

## FFmpeg e FFprobe — GPLv3

- Projeto e código-fonte: https://ffmpeg.org/ e https://github.com/FFmpeg/FFmpeg
- Origem da compilação Windows: https://www.gyan.dev/ffmpeg/builds/
- Compilação utilizada: `ffmpeg-release-essentials.zip`, da Gyan.
- Segundo o fornecedor, suas compilações estáticas são distribuídas sob **GPLv3**: https://www.gyan.dev/ffmpeg/builds/
- Texto da licença: https://www.gnu.org/licenses/gpl-3.0.html
- Informações oficiais sobre as obrigações de redistribuição: https://ffmpeg.org/legal.html

O ZIP portátil inclui `bin/ffmpeg.exe` e `bin/ffprobe.exe`, usados como executáveis externos. O pacote distribuído deve acompanhar o texto da GPLv3, a indicação de origem e a identificação exata da versão e configuração de compilação (`licencas/ffmpeg-versao-e-configuracao.txt`). O código-fonte correspondente pode ser obtido no projeto FFmpeg e na referência do fornecedor indicada acima. O responsável pela distribuição deve verificar a correspondência da versão e a disponibilidade da fonte por todo o período aplicável.

## PySide6 / Qt for Python

- Projeto, licenças e fontes: https://doc.qt.io/qtforpython-6/licenses.html
- Qt: https://www.qt.io/licensing/open-source-lgpl-obligations
- PySide6 contém bibliotecas sujeitas a condições LGPL/GPL/comerciais, conforme os componentes e a distribuição.
- Os módulos e bibliotecas dinâmicas ficam no pacote portátil, no diretório `_internal`. Devem ser preservados ao copiar o aplicativo.

## PyInstaller

- Projeto e licença: https://pyinstaller.org/en/stable/license.html

## Avisos gerais

- WhatsApp é marca de seus respectivos titulares. Este projeto não é afiliado ao WhatsApp ou à Meta.
- Referências a licenças não representam aconselhamento jurídico ou garantia automática de cumprimento de todas as obrigações. Antes de qualquer redistribuição pública, o distribuidor deve conferir as licenças e a oferta correspondente de código-fonte.
