# -*- coding: utf-8 -*-
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Generated code. DO NOT EDIT!
#
# Snippet for DeleteIndex
# NOTE: This snippet has been automatically generated for illustrative purposes only.
# It may require modifications to work in your environment.

# To install the latest published package dependency, execute the following:
#   python3 -m pip install google-cloud-datastore-admin


# [START datastore_generated_datastore_admin_v1_DatastoreAdmin_DeleteIndex_async]
from google.cloud import datastore_admin_v1


async def sample_delete_index():
    # Create a client
    client = datastore_admin_v1.DatastoreAdminAsyncClient()

    # Initialize request argument(s)
    request = datastore_admin_v1.DeleteIndexRequest(
    )

    # Make the request
    operation = client.delete_index(request=request)

    print("Waiting for operation to complete...")

    response = await operation.result()
    print(response)

# [END datastore_generated_datastore_admin_v1_DatastoreAdmin_DeleteIndex_async]
