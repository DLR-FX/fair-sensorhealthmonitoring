from fpdf import FPDF

class SetupPDF():
    def __init__(self):
        super(SetupPDF, self).__init__()
        self.pdf = FPDF(orientation = 'P', unit = 'mm', format='A4')
        self.pdf.add_page()
        self.pdf.set_font("Arial", size=10)

    def setContentPDF(self, warnings):
        for warning in warnings:
            self.pdf.cell(200,10, txt=warning, ln=1, align="C")
        self.pdf.output("Warnings.pdf")