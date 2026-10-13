'''Gera o ícone do Estoqium (assets/estoqium.ico).

Script de desenvolvimento: execute uma vez com `python assets/create_icon.py`.
Requer Pillow (apenas para gerar o ícone; não é dependência do aplicativo).
'''
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 256
BG = '#2563eb'
FG = '#ffffff'

img = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Fundo arredondado
margin = 8
draw.rounded_rectangle(
    [margin, margin, SIZE - margin, SIZE - margin],
    radius=48,
    fill=BG,
)

# Caixa de estoque estilizada
cx, cy = SIZE // 2, SIZE // 2
w, h = 130, 90
top = cy - h // 2
draw.rectangle([cx - w // 2, top, cx + w // 2, top + h], outline=FG, width=12)
draw.line([cx - w // 2, top + 28, cx + w // 2, top + 28], fill=FG, width=12)
draw.line([cx - 18, top, cx - 18, top + 28], fill=FG, width=10)
draw.line([cx + 18, top, cx + 18, top + 28], fill=FG, width=10)

out = Path(__file__).parent / 'estoqium.ico'
img.save(out, format='ICO', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f'Ícone gerado: {out}')
