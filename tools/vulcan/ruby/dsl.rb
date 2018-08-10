#!/usr/bin/ruby
#
# Generates a vulcan Project from simple DSL
#  because the json was too messy
#
# required gems: 
#  * json for ruby < 1.9
#  * ActiveSupport for OrderedHash
#
#
# Documentation of the vulcan format: https://git.spotify.net/cgit.cgi/vulcan.git/tree/doc/index.asciidoc
#
# DSL
#  Every method call is saved to a hash with the method name as key and the argument(s) as value, 
#   except these special helper calls
#  version - also adds the key 'major' with value of the characters before the first dot in the string passed to version
#  dependencies - the root node
#  package <package> - will be added under the "~" list in the current parent block
#   Helper intended for package to download
#   The key "package" will be defined with the value of the argument
#  group <description> - will be added under the "~" list in the current parent block
#   Helper intended for subconfiguration
#   The key "description" will be defined with the value of the argument
#
# Using: 
#  1. Make a new ruby script that requires the dsl
#  2. Write the dsl
#
#  ruby Example.rb > PROJECT
#
# Example.rb
=begin

VULCAN_PATH = "../vendor/vulcan/ruby"
require "#{VULCAN_PATH}/dsl"

dependencies do
  description "Defaults"
  format "zip"
  type "url"
  artifactory "https://artifactory.spotify.net/artifactory"
  client_artifactory "${artifactory}/client-infrastructure"
  binaries_server "https://binaries.spotify.net"
  package_id "null"
  check_package_id "false"
  action "copy"
  
  group "Stitch" do
    stitch_base "${client_artifactory}"
    id "${name}.${major}"
    path "binaries/apps/${id}"
    name "${package}"
    remote_path "${project}/${package}/${branch}/${version}"
    remote_file "${name}.${version}.${branch}.${build}.spa"
    url "${stitch_base}/${remote_path}/${remote_file}"
    branch "stable"
    
    group "Frameworks" do
      project "stitch-frameworks"
      
      package "views" do
        version "1.42.1"
        build "62576fc.80"
      end
      
      package "logging-utils" do
        version "0.0.11"
        build "36b952d.88"
        branch "master"
      end
      
      group "Frameworks in the apps repo" do
        project "stitch-apps"

        package "error" do
          version "1.0.0"
          build "f4ac9fc.6"
          branch "master"
        end

        package "install" do
          version "1.0.0"
          build "c6a6f29.14"
          branch "master"
        end
      end
    end
  end
end

=end

require "rubygems"
require "json"
require "active_support/ordered_hash"

module Vulcan
  class DSL
    self.methods.each do |method|
      next if method =~ /^__.+__$/
      next if %w(instance_eval instance_variable_get method_missing).include?(method.to_s)
      class_eval("""
      def #{method} *args
        method_missing :#{method}, *args
      end
      """)
    end
  
    def initialize values = {}
      @values = values
    end
  
    def self.call values = {}, &block
      instance = new(values)
      instance.instance_eval(&block)
      hash = instance.instance_variable_get("@values")
      ActiveSupport::OrderedHash[hash.sort_by { |k, v| k }]
    end
  
    def method_missing name, value
      @values[name.to_s] = value
    end
  end
  
  class DSL # Override kernel methods
    def format *args
      method_missing :format, *args
    end
  end

  class DSL # Helpers
    def package name, &block
      (@values["~"] ||= []) << DSL.call("package" => name.to_s, &block)
    end
  
    def group description, &block
      (@values["~"] ||= []) << DSL.call("description" => description.to_s, &block)
    end
  
    def version str
      major = str.split(".").first
      method_missing "version", str
      method_missing "major", major
    end
  end
end

def dependencies &block
  a = {
    "dependencies" => [Vulcan::DSL.call(&block)]
  }
  puts JSON.pretty_generate(a)
end
