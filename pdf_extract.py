#https://towardsdatascience.com/extracting-text-from-pdf-files-with-python-a-comprehensive-guide-9fc4003d517
#https://zhuanlan.zhihu.com/p/680175740
#https://github.com/g-stavrakis/PDF_Text_Extraction/blob/main/PDF_Reader.ipynb
#To read the PDF
import PyPDF2

from PyPDF2 import PageObject
#To analyze the PDF layout and extract text
from pdfminer.high_level import extract_text, extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTRect, LTFigure, LTPage

#To extract text from tables in PDF
import pdfplumber

#To extract the images from the PDF
from pdf2image import convert_from_path
#To use pdf2image, pls refer to this link to install poppler dependency on different system: https://stackoverflow.com/questions/53481088/poppler-in-path-for-pdf2image

#To remove the additional created files
import os


def text_extraction(elemetnt: LTTextContainer):
    #Extracting the text from the in-line text elemtent
    line_text = elemetnt.get_text()
    return line_text


#Create a function to crop the image elements from PDFs
def crop_image(element: LTFigure, pageObj:PageObject, save_file_name):
    #Get the coordinates to crop the image from the PDF
    [image_left, image_top, image_right, image_bottom] = [element.x0, element.y0, element.x1, element.y1]

    #crop the page using coordinates(left, bottom, right, top)
    pageObj.mediabox.lower_left = (image_left, image_bottom)
    pageObj.mediabox.upper_right = (image_right, image_top)

    #save the cropped page to a new PDF
    cropped_pdf_writer = PyPDF2.PdfWriter()
    cropped_pdf_writer.add_page(pageObj)

    #save the cropped PDF to a new file
    with open(save_file_name, 'wb') as cropped_pdf_file:
        cropped_pdf_writer.write(cropped_pdf_file)



#Create a function to conver the PDF to images
def convert_to_images(input_file, output_file, image_file_folder, poppler_path='D:\\ProgramFiles\\poppler-23.11.0\\Library\\bin'):
    images = convert_from_path(input_file, poppler_path=poppler_path)
    image = images[0]
    if not os.path.exists(image_file_folder):
        os.mkdir(image_file_folder)
    image.save(os.path.join(image_file_folder,output_file), "PNG")

#
#Extracting tables from the page
def extract_table(pdf_path, page_num, table_num):
    # Open the pdf file
    pdf = pdfplumber.open(pdf_path)
    # Find the examined page
    table_page = pdf.pages[page_num]
    # Extract the appropriate table
    table = table_page.extract_tables()[table_num]

    return table

#Convert table into the appropriate format
def table_convert(table):
    table_string = ''
    # Iterate through each row of the table
    for row_num in range(len(table)):
        row = table[row_num]
        # Remove the line breaker from the wrapted texts
        cleaned_row = [
            item.replace('\n', ' ') if item is not None and '\n' in item else 'None' if item is None else item for item
            in row]
        # Convert the table into a string
        table_string += ('|' + '|'.join(cleaned_row) + '|' + '\n')
    # Removing the last line break
    table_string = table_string[:-1]
    return table_string
def is_element_inside_any_table(element, page, tables):
    x0, y0up, x1, y1up = element.bbox
    y0 = page.bbox[3] - y1up
    y1 = page.bbox[3] - y0up

    for table in tables:
        tx0, ty0, tx1, ty1 = table.bbox
        if tx0 <= x0 <= x1 <= tx1 and ty0 <= y0 <= y1 <= ty1:
            return True
    return False

def find_table_for_element(element, page, tables):
    x0, y0up, x1, y1up = element.bbox
    # Change the cordinates because the pdfminer counts from the botton to top of the page
    y0 = page.bbox[3] - y1up
    y1 = page.bbox[3] - y0up
    for i, table in enumerate(tables):
        tx0, ty0, tx1, ty1 = table.bbox
        if tx0 <= x0 <= x1 <= tx1 and ty0 <= y0 <= y1 <= ty1:
            return i  # Return the index of the table
    return None



def pdf_process(pdf_path, image_extraced_file_name = "cropped_image.pdf", image_file_folder="extracted_images"):
    pdfFileObj = open(pdf_path, 'rb')
    pdfReaded = PyPDF2.PdfReader(pdfFileObj)

    #Create the dictionary to extract text from each image
    text_per_page = {}

    for pagenum, page in enumerate(extract_pages(pdf_path)):

        #Initialize the varibles needed for the text extraction from the page
        pageObj = pdfReaded.pages[pagenum]
        page_text = []
        text_from_tables = []
        image_save_path = [] #text_from_images
        page_content = []

        #Initialize the number of the examined tables
        # Initialize the number of the examined tables
        image_num = 0
        table_in_page = -1

        #Open the pdf file
        pdf = pdfplumber.open(pdf_path)
        #Find the examined page
        page_tables = pdf.pages[pagenum]
        #Find the number of tables on the page
        tables = page_tables.find_tables()
        if len(tables) != 0:
            table_in_page = 0
        for table_num in range(len(tables)):
            # Extract the information of the table
            table = extract_table(pdf_path, pagenum, table_num)
            # Convert the table information in structured string format
            table_string = table_convert(table)
            # Append the table string into a list
            text_from_tables.append(table_string)


        #Find all the elements
        page_elements = [(element.y1, element)for element in page._objs]
        page_elements.sort(key=lambda a:a[0], reverse=True)


        #Find the elements that composed a page
        for i, component in enumerate(page_elements):
            #Extract the element of the page layout
            element = component[1]

            if table_in_page == -1:
                pass
            else:
                if is_element_inside_any_table(element, page, tables):
                    table_found = find_table_for_element(element, page, tables)
                    if table_found == table_in_page and table_found != None:
                        page_content.append(text_from_tables[table_in_page])
                        page_text.append('table')
                        table_in_page += 1
                    # Pass this iteration because the content of this element was extracted from the tables
                    continue
            if not is_element_inside_any_table(element, page, tables):

                # Check if the element is text element
                if isinstance(element, LTTextContainer):
                    # Use the function to extract the text and format for each text element
                    line_text = text_extraction(element)
                    # Append the text of each line to the page text
                    page_text.append(line_text)
                    page_content.append(line_text)
                    # Check the elements for images

                #Check the elements for images
                if isinstance(element, LTFigure):

                    #Crop the image from the PDF
                    crop_image(element, pageObj,image_extraced_file_name)
                    #Convert the cropped pdf to an image
                    image_file_name = "page" + str(pagenum) + "_image" + str(image_num) + ".png"
                    image_num += 1
                    convert_to_images(image_extraced_file_name,image_file_name, image_file_folder)
                    image_save_path.append(image_file_name)

                    page_content.append(image_file_name)

                    #Add a placeholder in the text
                    page_text.append('image')


        #Create the key of the dictionary
        dctkey = "Page_" + str(pagenum)
        text_per_page[dctkey] = [page_text, image_save_path, text_from_tables, page_content]

    pdfFileObj.close()
    os.remove(image_extraced_file_name)
    return text_per_page

if __name__ == "__main__":
    text_per_page = pdf_process("test2.pdf")
    result = '\n'.join(text_per_page['Page_1'][3])
    print(result)
