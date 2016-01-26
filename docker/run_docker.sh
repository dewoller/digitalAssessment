docker run  \
-v $(pwd)/notebooks:/pandas/notebooks \
           -p 8000:8000                          \
           -ti include/pandas
