import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    return render_template('output.html')

@app.route('/search', methods=['GET'])
def search():
# Definisci l'URL della pagina web da scaricare
    term = request.args.get('term')
    url = f"https://www.immobiliare.it/vendita-case/{term}/?criterio=prezzo&ordine=asc"

    # Effettua una richiesta HTTP alla pagina web
    response = requests.get(url)
    data = {}
    seen_titles = set()
    # Verifica se la richiesta è andata a buon fine
    for i in range(1, 10):

        url += ('&pag=' + str(i))
        response = requests.get(url)
        if response.status_code == 200:
            # Parsing del contenuto HTML utilizzando BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print('Titolo della pagina:', soup.title.text)
            # Trova tutti gli elementi HTML che contengono i titoli delle notizie (questo è un esempio, potrebbe variare a seconda del sito)
            superficie = soup.find_all('li', class_='nd-list__item in-feat__item', attrs={'aria-label': "superficie"})
            prices = soup.find_all('div', class_='in-reListCardPrice')
            ids = soup.find_all('li', class_='nd-list__item in-reListItem in-realEstateResults__item')
            # Find all 'a' elements within the specified 'div' element
            links = soup.find_all('div', class_=['nd-mediaObject__content in-reListCard__content', 'nd-mediaObject__content in-reListCard__content is-spaced'])
            # Iterate over each link
            i = 0
            for link, price, oneid in zip(links, prices, ids):
                a_tag = link.find('a')
                if a_tag is not None:
                    id = oneid.get('id')
                    href = a_tag.get('href')  # Get the 'href' attribute
                    title = a_tag.get('title')  # Get the 'title' attribute
                    price_in_span = price.find('span')
                    superficie_element = link.find('li', attrs={'aria-label': "superficie"})
                    if superficie_element is not None:
                        superficie_text =  int(superficie_element.text.replace("m²", "").replace(".", ""))
                    else :
                        superficie_text = -1
                    if price_in_span is not None:
                        price_text = price_in_span.text
                        if price_text == "Prezzo su richiesta":
                            price_text = str(-1)
                        int_price = int(price_text.replace("€", "").replace(".", "").replace(" ", "").replace("da", "").split(",")[0])
                    # Add the data to the dictionary
                    definiteve_price = int_price / int(superficie_text)
                    data[id] = {'Title': title, 'Link': href,'Prezzo al m2' : (definiteve_price if definiteve_price > 0 else -1), 'Superficie': superficie_text if superficie_text > 0 else 'N/A' , 'Price': price_text}
                    seen_titles.add(title)
            # Print the data

        else:
            print('Errore nella richiesta HTTP:', response.status_code)

    sorted_data = sorted(data.items(), key=lambda x: x[1]['Prezzo al m2'])

    # for id, info in sorted_data:
    #     print(f'title: {info["Title"]}, Link: {info["Link"]}, Prezzo al m²: {info["Prezzo al m2"]}, Superficie: {info["Superficie"]}, Price: {info["Price"]}')
    html_content = "<html><body><table>"

    # Add table headers
    html_content += "<tr><th>Immobile</th><th>Link</th><th>Prezzo al m²</th><th>Superficie</th><th>Prezzo Totale</th></tr>"

    for id, info in sorted_data:
        value = info['Prezzo al m2'] if info['Prezzo al m2'] < 1 else round(info['Prezzo al m2'])
        html_content += f'<tr><td>{info["Title"]}</td><td><a target="_blank" href="{info["Link"]}">Link</a></td><td>{value if value > 0 else "N/A"} €/m² </td><td>{info["Superficie"]}</td><td>{info["Price"] if info["Price"] > "0" else "Prezzo su Richiesta"}</td></tr>'

    html_content += "</table></body></html>"

    # Write the HTML content to a file
    with open('templates/output.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    return redirect(url_for('data'))

if __name__ == '__main__':
    app.run(debug=True)