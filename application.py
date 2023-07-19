from flask import Flask, request, jsonify, render_template
from flask_cors import CORS, cross_origin
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import logging
import requests
import pymongo

logging.basicConfig(filename="scrapper.log", level=logging.DEBUG)

app = Flask(__name__)

@app.route("/", methods=['GET'])
@cross_origin()
def homepage():
    return render_template("index.html")

@app.route("/review", methods=['POST', 'GET'])
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ", "")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = urlopen(flipkart_url)
            flipkart_page = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkart_page, "html.parser")
            bigboxes = flipkart_html.find_all("div", {"class": "_1AtVbE col-12-12"})
            del bigboxes[0:3]
            del bigboxes[-1]
            del bigboxes[-1]
            del bigboxes[-1]
            del bigboxes[-1]

            reviews = []
            filename = searchString + ".csv"
            fw = open(filename, "w")
            headers = "Product, Price, Customer Name, Rating, Comment\n"
            fw.write(headers)

            for box in bigboxes:
                product_link = "https://www.flipkart.com" + box.div.div.div.a['href']
                product_req = requests.get(product_link)
                product_req.encoding = 'utf-8'
                product_html = bs(product_req.text, "html.parser")

                try:
                    product_name = product_html.find("span", {"class": "B_NuCI"}).text
                except:
                    product_name = "N/A"
                    logging.info("product_name")

                try:
                    product_price = product_html.find("div", {"class": "_30jeq3 _16Jk6d"}).text
                except:
                    product_price = "N/A"
                    logging.info("product_price")

                comment_boxes = product_html.find_all('div', {'class': "_16PBlm"})

                for comment_box in comment_boxes:
                    try:
                        name = comment_box.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                    except:
                        name = "N/A"
                        logging.info("name")

                    try:
                        rating = comment_box.div.div.div.div.text
                    except:
                        rating = "No Rating"
                        logging.info('rating')

                    try:
                         comment = comment_box.div.div.find('div', {'class': ''}).text.strip()
                    except Exception as e:
                        comment = "N/A"
                        logging.info(e)

                    fw.write(f"{product_name}, {product_price}, {name}, {rating}, {comment}\n")

                    mydict = {
                        "Product": product_name,
                        "Price": product_price,
                        "Customer Name": name,
                        "Rating": rating,
                        "Comment": comment
                    }
                    reviews.append(mydict)

            fw.close()
            logging.info("log my final result {}".format(reviews))

            client = pymongo.MongoClient("mongodb+srv://apurbamaji3013:apurba123@cluster0.9qwzsya.mongodb.net/?retryWrites=true&w=majority")
            db = client['Flipkart_reviews']
            review_col = db["Records"]
            review_col.insert_many(reviews)

            return render_template('result.html', reviews=reviews[0:(len(reviews)-1)])

        except Exception as e:
            logging.error(e)
            return 'Something went wrong'
    else:
        return render_template('index.html')

if __name__ == '__main__':
    # app.run(host="0.0.0.0")
    app.run(host='127.0.0.1', port=8000, debug=True)