/*
 * Copyright (c) 2017 Spotify AB.
 *
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

#include <NFHTTP/NFHTTP.h>

#include <fstream>
#include <iostream>

#include <nlohmann/json.hpp>

int main(int argc, char *argv[]) {
  // Parse our arguments
  std::string input_json_file = "";
  std::string output_directory = "";
  for (int i = 1; i < argc; ++i) {
    std::string arg_string = argv[i];
    if (arg_string == "-i") {
      input_json_file = argv[++i];
    } else if (arg_string == "-o") {
      output_directory = argv[++i];
    }
  }

  // Create our client
  auto client = nativeformat::http::createClient(nativeformat::http::standardCacheLocation(),
                                                 "NFHTTP-" + nativeformat::http::version());

  // Setup our responses array
  nlohmann::json output_json;
  nlohmann::json responses_json;
  std::ofstream output_file(output_directory + "/responses.json");

  // Parse the requests json
  std::ifstream input_json_stream(input_json_file);
  nlohmann::json input_json = nlohmann::json::parse(input_json_stream);
  auto requests = input_json["requests"];
  for (auto it = requests.begin(); it != requests.end(); ++it) {
    const std::string url = (*it)["url"];
    const std::string id = (*it)["id"];

    // Send our request
    auto request = nativeformat::http::createRequest(url, {});
    auto response = client->performRequestSynchronously(request);
    size_t data_length = 0;
    const unsigned char *data = response->data(data_length);

    // Generate a random file to dump the payload to
    const size_t random_file_length = 20;
    auto randchar = []() {
      const char charset[] =
          "0123456789"
          "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
          "abcdefghijklmnopqrstuvwxyz";
      const size_t max_index = (sizeof(charset) - 1);
      return charset[rand() % max_index];
    };
    std::string random_file_name(random_file_length, 0);
    std::generate_n(random_file_name.begin(), random_file_length, randchar);
    random_file_name.insert(0, "/");
    random_file_name.insert(0, output_directory);
    std::ofstream random_file;
    random_file.open(random_file_name);
    random_file.write((const char *)data, data_length);
    random_file.close();

    // Create our response JSON
    nlohmann::json response_json = {{"payload", random_file_name}};
    responses_json[id] = response_json;
  }

  // Write out responses JSON to disk
  output_json["responses"] = responses_json;
  output_file << std::setw(4) << output_json << std::endl;

  return 0;
}
