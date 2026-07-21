from PIL import Image, ImageDraw, ImageFont

font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)

# ---------- SLIGHT VARIATION ----------
img1 = Image.new('RGB', (800, 400), color='white')
draw1 = ImageDraw.Draw(img1)
draw1.text((50, 100),
           "Name: Ramesh Patilkar\nSurvey: MH-1234\nAadhaar: 1234 5678 9012",
           fill='black', font=font)
img1.save("variation.jpg")


# ---------- FRAUD CASE ----------
img2 = Image.new('RGB', (800, 400), color='white')
draw2 = ImageDraw.Draw(img2)
draw2.text((50, 100),
           "Name: XYZ ABC\nSurvey: MH-1234\nAadhaar: 1234 5678 9012",
           fill='black', font=font)
img2.save("fraud.jpg")

print("Variation and Fraud test images created!")