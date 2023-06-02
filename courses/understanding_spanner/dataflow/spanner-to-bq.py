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

import argparse
import logging
import re, os
from typing import NamedTuple, List

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.io.gcp.spanner import ReadFromSpanner


class PetRow(NamedTuple):
    OwnerID: str
    PetName: str
    PetType: str
    Breed: str

beam.coders.registry.register_coder(PetRow, beam.coders.RowCoder)

def main(argv=None, save_main_session=True):
    """Main entry point."""
    projectid = os.environ.get('GOOGLE_CLOUD_PROJECT')
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--instance',
        dest='instance',
        default='test-spanner-instance',
        help='Spanner instance ID.')
    parser.add_argument(
        '--database',
        dest='database',
        default = 'pets-db',      
        help='Spanner database.')
    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = save_main_session

    with beam.Pipeline(options=pipeline_options) as p:
        owner_pets = p | ReadFromSpanner(
                            project_id=projectid,
                            instance_id=known_args.instance,
                            database_id=known_args.database,
                            row_type=PetRow,
                            sql = "SELECT OwnerID, PetName, PetType, Breed FROM Pets"
                            ).with_output_types(PetRow)
                            
        ( owner_pets | beam.Map(lambda x : x._asdict())
                     | beam.io.WriteToBigQuery('Pets', dataset = 'petsdb', project = projectid, method = 'STREAMING_INSERTS')
        )
        owner_pets | beam.Map(print)  

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  main()
