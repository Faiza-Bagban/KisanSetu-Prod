# -----------------------------
# Resolution Time ML Model
# -----------------------------

from sklearn.tree import DecisionTreeRegressor
import numpy as np


# Training Dataset
# Feature = category score
# Target = days

X = np.array([
    [1],  # payment issue
    [2],  # document rejection
    [3],  # officer misconduct
    [4],  # scheme delay
    [5]   # other
])

y = np.array([
    10,
    4,
    18,
    12,
    6
])


# Train Model
model = DecisionTreeRegressor()
model.fit(X, y)


CATEGORY_ENCODING = {
    "payment issue": 1,
    "document rejection": 2,
    "officer misconduct": 3,
    "scheme delay": 4,
    "other": 5
}


def predict_resolution_ml(category: str):

    category_value = CATEGORY_ENCODING.get(category, 5)

    prediction = model.predict([[category_value]])

    days = round(float(prediction[0]))

    return f"{days} working days"