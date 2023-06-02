#  Copyright (C) 2023 Google Inc.
# 
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from google.cloud import spanner

instance_id = 'test-spanner-instance'
database_id = 'pets-db'

client = spanner.Client()
instance = client.instance(instance_id)
database = instance.database(database_id)

def spanner_get_pets(request):
    query = """SELECT OwnerName, PetName, PetType, Breed 
         FROM Owners 
         JOIN Pets ON Owners.OwnerID = Pets.OwnerID;"""

    outputs = []
    with database.snapshot() as snapshot:
        results = snapshot.execute_sql(query)
        output = '<div>OwnerName,PetName,PetType,Breed</div>'
        outputs.append(output)
        for row in results:
            output = '<div>{},{},{},{}</div>'.format(*row)
            outputs.append(output)

    return '\n'.join(outputs)
