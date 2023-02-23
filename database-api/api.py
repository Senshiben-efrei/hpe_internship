# import libraries
import pandas as pd
import numpy as np

import flask

file = '../src/data/data.csv'

# create a read request to get the data from the csv file
def read_data():
    # if the csv file does not exist, create it
    try:
        df = pd.read_csv(file)
    except:
        df = pd.DataFrame(columns=['purchase order number','Partner','Distributor','Client','Status', 'Bundle config id','Product number','quantity','Description','Unit Price','Total Cost'])
        df.to_csv(file, index=False)
    return df.to_dict('records')

# if an add request is made, add the data to the csv file
def add_data(data):
    df = pd.read_csv(file)
    df = df.append(data, ignore_index=True)
    df.to_csv(file, index=False)

# delete row from csv file by index
def delete_data(index):
    df = pd.read_csv(file)
    df = df.drop(index)
    df.to_csv(file, index=False)

# create a update request to update the data in the csv file
def update_data(index, data):
    df = pd.read_csv(file)
    # if a input is not given, keep the old value
    for key in data:
        if data[key] == '':
            data[key] = df.loc[index][key]
    df.loc[index] = data
    df.to_csv(file, index=False)



# create a flask app
app = flask.Flask(__name__)
app.config["DEBUG"] = True



# create a route to get the data
@app.route('/api/v1/resources/data/all', methods=['GET'])
def api_all():
    return flask.jsonify(read_data())

# create a route to add data
@app.route('/api/v1/resources/data/add', methods=['POST'])
def api_add():
    data = flask.request.json
    add_data(data)
    return flask.jsonify(data)

# create a route to delete data
@app.route('/api/v1/resources/data/delete/<int:index>', methods=['DELETE'])
def api_delete(index):
    delete_data(index)
    return flask.jsonify({"message": "deleted"})

# create a route to update data
@app.route('/api/v1/resources/data/update/<int:index>', methods=['PUT'])
def api_update(index):
    data = flask.request.json
    update_data(index, data)
    return flask.jsonify({"message": "updated"})



# run the app
app.run()
