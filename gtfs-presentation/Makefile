# Makefile for GTFS presentation using pandoc and beamer

# Variables
PRESENTATION = presentation
OUTPUT_DIR = output
PDF_OUTPUT = $(OUTPUT_DIR)/$(PRESENTATION).pdf

# Default target
all: $(PDF_OUTPUT)

# Create output directory if it doesn't exist
$(OUTPUT_DIR):
	mkdir -p $(OUTPUT_DIR)

# Compile presentation to PDF using beamer
$(PDF_OUTPUT): $(PRESENTATION).md | $(OUTPUT_DIR)
	pandoc $(PRESENTATION).md \
		-t beamer \
		-o $(PDF_OUTPUT) \
		--pdf-engine=pdflatex \
		--slide-level=2

# Clean generated files
clean:
	rm -rf $(OUTPUT_DIR)

# Open the generated PDF (Linux)
view: $(PDF_OUTPUT)
	xdg-open $(PDF_OUTPUT)

# Rebuild everything
rebuild: clean all

.PHONY: all clean view rebuild