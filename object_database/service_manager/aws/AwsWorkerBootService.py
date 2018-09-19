#   Copyright 2018 Braxton Mckee
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import traceback
import logging
import time
import boto3
import uuid
import base64
import json
import sys
import time
import os.path
import logging
import traceback
import datetime
import os

from typed_python import OneOf
from object_database import ServiceBase, service_schema, Schema, Indexed
from object_database.web import cells
from nativepython.python.string_util import closest_N_in

schema = Schema("core.AwsWorkerBootService")

valid_instance_types = {
    'm1.small': {'RAM':1.7,'CPU':1,'COST':0.044},
    'm1.medium': {'RAM':3.75,'CPU':1,'COST':0.087},
    'm1.large': {'RAM':7.5,'CPU':2,'COST':0.175},
    'm1.xlarge': {'RAM':15,'CPU':4,'COST':0.35},
    'c1.medium': {'RAM':1.7,'CPU':2,'COST':0.13},
    'c1.xlarge': {'RAM':7,'CPU':8,'COST':0.52},
    'cc2.8xlarge': {'RAM':60.5,'CPU':32,'COST':2},
    'm2.xlarge': {'RAM':17.1,'CPU':2,'COST':0.245},
    'm2.2xlarge': {'RAM':34.2,'CPU':4,'COST':0.49},
    'm2.4xlarge': {'RAM':68.4,'CPU':8,'COST':0.98},
    'hs1.8xlarge': {'RAM':117,'CPU':16,'COST':4.6},
    'm5.large': {'RAM':8,'CPU':2,'COST':0.096},
    'm5.xlarge': {'RAM':16,'CPU':4,'COST':0.192},
    'm5.2xlarge': {'RAM':32,'CPU':8,'COST':0.384},
    'm5.4xlarge': {'RAM':64,'CPU':16,'COST':0.768},
    'm5.12xlarge': {'RAM':192,'CPU':48,'COST':2.304},
    'm5.24xlarge': {'RAM':384,'CPU':96,'COST':4.608},
    'm4.large': {'RAM':8,'CPU':2,'COST':0.1},
    'm4.xlarge': {'RAM':16,'CPU':4,'COST':0.2},
    'm4.2xlarge': {'RAM':32,'CPU':8,'COST':0.4},
    'm4.4xlarge': {'RAM':64,'CPU':16,'COST':0.8},
    'm4.10xlarge': {'RAM':160,'CPU':40,'COST':2},
    'm4.16xlarge': {'RAM':256,'CPU':64,'COST':3.2},
    'c5.large': {'RAM':4,'CPU':2,'COST':0.085},
    'c5.xlarge': {'RAM':8,'CPU':4,'COST':0.17},
    'c5.2xlarge': {'RAM':16,'CPU':8,'COST':0.34},
    'c5.4xlarge': {'RAM':32,'CPU':16,'COST':0.68},
    'c5.9xlarge': {'RAM':72,'CPU':36,'COST':1.53},
    'c5.18xlarge': {'RAM':144,'CPU':72,'COST':3.06},
    'c4.large': {'RAM':3.75,'CPU':2,'COST':0.1},
    'c4.xlarge': {'RAM':7.5,'CPU':4,'COST':0.199},
    'c4.2xlarge': {'RAM':15,'CPU':8,'COST':0.398},
    'c4.4xlarge': {'RAM':30,'CPU':16,'COST':0.796},
    'c4.8xlarge': {'RAM':60,'CPU':36,'COST':1.591},
    'r5.large': {'RAM':16,'CPU':2,'COST':0.126},
    'r5.xlarge': {'RAM':32,'CPU':4,'COST':0.252},
    'r5.2xlarge': {'RAM':64,'CPU':8,'COST':0.504},
    'r5.4xlarge': {'RAM':128,'CPU':16,'COST':1.008},
    'r5.12xlarge': {'RAM':384,'CPU':48,'COST':3.024},
    'r5.24xlarge': {'RAM':768,'CPU':96,'COST':6.047},
    'r4.large': {'RAM':15.25,'CPU':2,'COST':0.133},
    'r4.xlarge': {'RAM':30.5,'CPU':4,'COST':0.266},
    'r4.2xlarge': {'RAM':61,'CPU':8,'COST':0.532},
    'r4.4xlarge': {'RAM':122,'CPU':16,'COST':1.064},
    'r4.8xlarge': {'RAM':244,'CPU':32,'COST':2.128},
    'r4.16xlarge': {'RAM':488,'CPU':64,'COST':4.256},
    'p3.2xlarge': {'RAM':61,'CPU':8,'COST':3.06},
    'p3.8xlarge': {'RAM':244,'CPU':32,'COST':12.24},
    'p3.16xlarge': {'RAM':488,'CPU':64,'COST':24.48},
    'p2.xlarge': {'RAM':61,'CPU':4,'COST':0.9},
    'p2.8xlarge': {'RAM':488,'CPU':32,'COST':7.2},
    'p2.16xlarge': {'RAM':732,'CPU':64,'COST':14.4},
    'g3.4xlarge': {'RAM':122,'CPU':16,'COST':1.14},
    'g3.8xlarge': {'RAM':244,'CPU':32,'COST':2.28},
    'g3.16xlarge': {'RAM':488,'CPU':64,'COST':4.56},
    'h1.2xlarge': {'RAM':32,'CPU':8,'COST':0.468},
    'h1.4xlarge': {'RAM':64,'CPU':16,'COST':0.936},
    'h1.8xlarge': {'RAM':128,'CPU':32,'COST':1.872},
    'h1.16xlarge': {'RAM':256,'CPU':64,'COST':3.744},
    'd2.xlarge': {'RAM':30.5,'CPU':4,'COST':0.69},
    'd2.2xlarge': {'RAM':61,'CPU':8,'COST':1.38},
    'd2.4xlarge': {'RAM':122,'CPU':16,'COST':2.76},
    'd2.8xlarge': {'RAM':244,'CPU':36,'COST':5.52},
    'm3.medium': {'RAM':3.75,'CPU':1,'COST':0.067},
    'm3.large': {'RAM':7.5,'CPU':2,'COST':0.133},
    'm3.xlarge': {'RAM':15,'CPU':4,'COST':0.266},
    'm3.2xlarge': {'RAM':30,'CPU':8,'COST':0.532},
    'c3.large': {'RAM':3.75,'CPU':2,'COST':0.105},
    'c3.xlarge': {'RAM':7.5,'CPU':4,'COST':0.21},
    'c3.2xlarge': {'RAM':15,'CPU':8,'COST':0.42},
    'c3.4xlarge': {'RAM':30,'CPU':16,'COST':0.84},
    'c3.8xlarge': {'RAM':60,'CPU':32,'COST':1.68},
    'g2.2xlarge': {'RAM':15,'CPU':8,'COST':0.65},
    'g2.8xlarge': {'RAM':60,'CPU':32,'COST':2.6},
    'cr1.8xlarge': {'RAM':244,'CPU':32,'COST':3.5},
    'x1.16xlarge': {'RAM':976,'CPU':64,'COST':6.669},
    'x1.32xlarge': {'RAM':1952,'CPU':128,'COST':13.338},
    'x1e.xlarge': {'RAM':122,'CPU':4,'COST':0.834},
    'x1e.2xlarge': {'RAM':244,'CPU':8,'COST':1.668},
    'x1e.4xlarge': {'RAM':488,'CPU':16,'COST':3.336},
    'x1e.8xlarge': {'RAM':976,'CPU':32,'COST':6.672},
    'x1e.16xlarge': {'RAM':1952,'CPU':64,'COST':13.344},
    'x1e.32xlarge': {'RAM':3904,'CPU':128,'COST':26.688},
    'r3.large': {'RAM':15.25,'CPU':2,'COST':0.166},
    'r3.xlarge': {'RAM':30.5,'CPU':4,'COST':0.333},
    'r3.2xlarge': {'RAM':61,'CPU':8,'COST':0.665},
    'r3.4xlarge': {'RAM':122,'CPU':16,'COST':1.33},
    'r3.8xlarge': {'RAM':244,'CPU':32,'COST':2.66},
    'i2.xlarge': {'RAM':30.5,'CPU':4,'COST':0.853},
    'i2.2xlarge': {'RAM':61,'CPU':8,'COST':1.705},
    'i2.4xlarge': {'RAM':122,'CPU':16,'COST':3.41},
    'i2.8xlarge': {'RAM':244,'CPU':32,'COST':6.82},
    'm5d.large': {'RAM':8,'CPU':2,'COST':0.113},
    'm5d.xlarge': {'RAM':16,'CPU':4,'COST':0.226},
    'm5d.2xlarge': {'RAM':32,'CPU':8,'COST':0.452},
    'm5d.4xlarge': {'RAM':64,'CPU':16,'COST':0.904},
    'm5d.12xlarge': {'RAM':192,'CPU':48,'COST':2.712},
    'm5d.24xlarge': {'RAM':384,'CPU':96,'COST':5.424},
    'c5d.large': {'RAM':4,'CPU':2,'COST':0.096},
    'c5d.xlarge': {'RAM':8,'CPU':4,'COST':0.192},
    'c5d.2xlarge': {'RAM':16,'CPU':8,'COST':0.384},
    'c5d.4xlarge': {'RAM':32,'CPU':16,'COST':0.768},
    'c5d.9xlarge': {'RAM':72,'CPU':36,'COST':1.728},
    'c5d.18xlarge': {'RAM':144,'CPU':72,'COST':3.456},
    'r5d.large': {'RAM':16,'CPU':2,'COST':0.144},
    'r5d.xlarge': {'RAM':32,'CPU':4,'COST':0.288},
    'r5d.2xlarge': {'RAM':64,'CPU':8,'COST':0.576},
    'r5d.4xlarge': {'RAM':128,'CPU':16,'COST':1.152},
    'r5d.12xlarge': {'RAM':384,'CPU':48,'COST':3.456},
    'r5d.24xlarge': {'RAM':768,'CPU':96,'COST':6.912},
    'z1d.large': {'RAM':16,'CPU':2,'COST':0.186},
    'z1d.xlarge': {'RAM':32,'CPU':4,'COST':0.372},
    'z1d.2xlarge': {'RAM':64,'CPU':8,'COST':0.744},
    'z1d.3xlarge': {'RAM':96,'CPU':12,'COST':1.116},
    'z1d.6xlarge': {'RAM':192,'CPU':24,'COST':2.232},
    'z1d.12xlarge': {'RAM':384,'CPU':48,'COST':4.464},
    'f1.2xlarge': {'RAM':122,'CPU':8,'COST':1.65},
    'f1.16xlarge': {'RAM':976,'CPU':64,'COST':13.2},
    'i3.large': {'RAM':15.25,'CPU':2,'COST':0.156},
    'i3.xlarge': {'RAM':30.5,'CPU':4,'COST':0.312},
    'i3.2xlarge': {'RAM':61,'CPU':8,'COST':0.624},
    'i3.4xlarge': {'RAM':122,'CPU':16,'COST':1.248},
    'i3.8xlarge': {'RAM':244,'CPU':32,'COST':2.496},
    'i3.16xlarge': {'RAM':488,'CPU':64,'COST':4.992}
    }
















@schema.define
class Configuration:
    db_hostname = str          #hostname to connect back to
    db_port = int              #port to connect back to
    region = str               #region to boot into
    vpc_id = str               #id of vpc to boot into
    subnet = str               #id of subnet to boot into
    security_group = str       #id of security group to boot into
    keypair = str              #security keypair name to use
    worker_name = str          #name of workers. This should be unique to this install.
    worker_iam_role_name = str #AIM role to boot workers into
    linux_ami = str            #default linux AMI to use when booting linux workers
    defaultStorageSize =  int  #gb of disk to mount on booted workers (if they need ebs)

    max_to_boot = int          #maximum number of workers we'll boot

@schema.define
class State:
    instance_type = Indexed(str)

    booted = int
    desired = int
    observedLimit = OneOf(None, int) #maximum observed limit count
    capacityConstrained = bool

own_dir = os.path.split(__file__)[0]

linux_bootstrap_script = open(os.path.join(own_dir, "aws_linux_bootstrap.sh"), "r").read()

class AwsApi:
    def __init__(self):
        self.config = Configuration.lookupAny()
        if not self.config:
            raise Exception("Please configure the aws service.")

        self.ec2 = boto3.resource('ec2',region_name=self.config.region)
        self.ec2_client = boto3.client('ec2',region_name=self.config.region)
        self.s3 = boto3.resource('s3',region_name=self.config.region)
        self.s3_client = boto3.client('s3',region_name=self.config.region)

    def allRunningInstances(self, includePending=True):
        filters = [{  
            'Name': 'tag:Name',
            'Values': [self.config.worker_name]
            }]

        res = {}

        for reservations in self.ec2_client.describe_instances(Filters=filters)["Reservations"]:
            for instance in reservations["Instances"]:
                if instance['State']['Name'] in ('running','pending') if includePending else ('running',):
                    res[str(instance["InstanceId"])] = instance

        return res

    def isInstanceWeOwn(self, instance):
        #make sure this instance is definitely one we booted.

        if not [t for t in instance.tags if t["Key"] == "Name" and t["Value"] == self.config.worker_name]:
            return False

        if instance.subnet.id != self.config.subnet:
            return False

        if not [t for t in instance.security_groups if t['GroupId'] == self.config.security_group]:
            return False

        if instance.key_pair.name != self.config.keypair:
            return False
        
        return True

    def terminateInstanceById(self, id):
        instance = self.ec2.Instance(id)
        assert self.isInstanceWeOwn(instance)
        logging.info("Terminating AWS instance %s", instance)
        instance.terminate()

    def bootWorker(self, 
            instanceType,
            clientToken=None,
            amiOverride=None,
            bootScriptOverride=None,
            nameValueOverride=None,
            extraTags=None,
            wantsTerminateOnShutdown=True
            ):
        boot_script = (
            linux_bootstrap_script.format(
                db_hostname=self.config.db_hostname,
                db_port=self.config.db_port
                )
            )

        if clientToken is None:
            clientToken = str(uuid.uuid4())

        if amiOverride is not None:
            ami = amiOverride
        else:
            ami = self.config.linux_ami

        def has_ephemeral_storage(instanceType):
            for t in ['m3', 'c3', 'x1', 'r3', 'f1', 'h1', 'i3', 'd2']:
                if instanceType.startswith(t):
                    return True
            return False

        if has_ephemeral_storage(instanceType):
            deviceMapping = {
                'DeviceName': '/dev/xvdb',
                'VirtualName': "ephemeral0"
                }
        else:
            deviceMapping = {
                'DeviceName': '/dev/xvdb',
                'VirtualName': "ephemeral0",
                "Ebs": {
                    "Encrypted": False,
                    "DeleteOnTermination": True,
                    "VolumeSize": self.config.defaultStorageSize,
                    "VolumeType": "gp2"
                    }
                }

        nameValue = nameValueOverride or self.config.worker_name

        return str(self.ec2.create_instances(
            ImageId=ami,
            InstanceType=instanceType,
            KeyName=self.config.keypair,
            MaxCount=1,
            MinCount=1,
            SecurityGroupIds=[self.config.security_group],
            SubnetId=self.config.subnet,
            ClientToken=clientToken,
            InstanceInitiatedShutdownBehavior='terminate' if wantsTerminateOnShutdown else "stop",
            IamInstanceProfile={'Name': self.config.worker_iam_role_name},
            UserData=boot_script, #base64.b64encode(boot_script.encode("ASCII")),
            BlockDeviceMappings=[deviceMapping],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [{ 
                        "Key": 'Name', 
                        "Value": nameValue
                        }] + [{ "Key": k, "Value": v} for (k,v) in (extraTags or {}).items()]
                }]
            )[0].id)


class AwsWorkerBootService(ServiceBase):
    def __init__(self, db, serviceInstance, serviceRuntimeConfig):
        ServiceBase.__init__(self, db, serviceInstance, serviceRuntimeConfig)

        self.SLEEP_INTERVAL = 10.0

    @staticmethod
    def currentTargets():
        return {s.instance_type: s.desired for s in State.lookupAll()}

    @staticmethod
    def currentBooted():
        return {s.instance_type: s.booted for s in State.lookupAll()}

    @staticmethod
    def setBootState(instance_type, target):
        if instance_type not in valid_instance_types:
            raise Exception(
                "Instance type %s is not a valid instance type. Did you mean one of %s?" % (
                    instance_type,
                    closest_N_in(instance_type, valid_instance_types, 3)
                    )
                )

        s = State.lookupAny(instance_type=instance_type)
        if not s:
            s = State(instance_type=instance_type)
        s.desired = target

    @staticmethod
    def bootOneDirectly(instance_type):
        AwsApi().bootWorker(instance_type)

    @staticmethod
    def shutdownAll():
        for s in State.lookupAll():
            s.desired = 0

    @staticmethod
    def shutOneDown(instance_type):
        api = AwsApi()
        i = [x for x in AwsApi.allRunningInstances().values() if x['InstanceType'] == instance_type]
        if not i:
            raise Exception("No instances of type %s are booted." % instance_type)
        else:
            logging.info("Terminating instance %s", i["InstanceId"])

        AwsApi().terminateInstanceById(i[0])

    @staticmethod
    def configure(
            db_hostname,
            db_port,
            region,
            vpc_id,
            subnet,
            security_group,
            keypair,
            worker_name,
            worker_iam_role_name,
            linux_ami,
            defaultStorageSize,
            max_to_boot
            ):
        c = Configuration.lookupAny()
        if not c:
            c = Configuration()

        if db_hostname is not None:
            c.db_hostname = db_hostname
        if db_port is not None:
            c.db_port = db_port
        if region is not None:
            c.region = region
        if vpc_id is not None:
            c.vpc_id = vpc_id
        if subnet is not None:
            c.subnet = subnet
        if security_group is not None:
            c.security_group = security_group
        if keypair is not None:
            c.keypair = keypair
        if worker_name is not None:
            c.worker_name = worker_name
        if worker_iam_role_name is not None:
            c.worker_iam_role_name = worker_iam_role_name
        if linux_ami is not None:
            c.linux_ami = linux_ami
        if defaultStorageSize is not None:
            c.defaultStorageSize = defaultStorageSize
        if max_to_boot is not None:
            c.max_to_boot = max_to_boot

    def setBootCount(self, instance_type, count):
        state = State.lookupAny(instance_type=instType)
        if not state:
            state = State(instance_type=instType)
        state.desired = count

    def initialize(self):
        self.db.subscribeToSchema(schema)

        with self.db.transaction():
            self.api = AwsApi()

    def doWork(self, shouldStop):
        while not shouldStop.is_set():
            try:
                if not self.pushTaskLoopForward():
                    time.sleep(1.0)
            except:
                logging.error("Failed: %s", traceback.format_exc())
                time.sleep(5.0)



    @staticmethod
    def serviceDisplay(serviceObject):
        cells.ensureSubscribedType(Configuration)
        cells.ensureSubscribedType(State)
        
        c = Configuration.lookupAny()

        if not c:
            return cells.Card("No configuration defined for  AWS")

        def bootCountSetter(state, ct):
            def f():
                state.desired = ct
            return f

        return cells.Grid(
            colFun=lambda: ['Instance Type', 'COST', 'RAM', 'CPU', 'Booted', 'Desired','ObservedLimit', 'CapacityConstrained'],
            rowFun=lambda: sorted(State.lookupAll(), key=lambda s:s.instance_type),
            headerFun=lambda x: x,
            rowLabelFun=None,
            rendererFun=lambda s,field: cells.Subscribed(lambda: 
                s.instance_type if field == 'Instance Type' else
                s.booted  if field == 'Booted' else 
                cells.Dropdown(str(s.desired), [(str(ct), bootCountSetter(s, ct)) for ct in list(range(10)) + list(range(10,101,10))]) 
                        if field == 'Desired' else 
                ("" if s.observedLimit is None else s.observedLimit) if field == 'ObservedLimit' else 
                ("Yes" if s.capacityConstrained else "") if field == 'CapacityConstrained' else 
                valid_instance_types[s.instance_type]['COST'] if field == 'COST' else 
                valid_instance_types[s.instance_type]['RAM'] if field == 'RAM' else 
                valid_instance_types[s.instance_type]['CPU'] if field == 'CPU' else 
                ""
                )
            ) + cells.Card(
                cells.Text("db_hostname = " + str(c.db_hostname)) + 
                cells.Text("db_port = " + str(c.db_port)) + 
                cells.Text("region = " + str(c.region)) + 
                cells.Text("vpc_id = " + str(c.vpc_id)) + 
                cells.Text("subnet = " + str(c.subnet)) + 
                cells.Text("security_group = " + str(c.security_group)) + 
                cells.Text("keypair = " + str(c.keypair)) + 
                cells.Text("worker_name = " + str(c.worker_name)) + 
                cells.Text("worker_iam_role_name = " + str(c.worker_iam_role_name)) + 
                cells.Text("linux_ami = " + str(c.linux_ami)) + 
                cells.Text("defaultStorageSize = " + str(c.defaultStorageSize)) + 
                cells.Text("max_to_boot = " + str(c.max_to_boot))
                )

    def pushTaskLoopForward(self):
        with self.db.view():
            actuallyUsed = self.api.allRunningInstances()

        instanceTypes = {}
        instancesByType = {}

        for machineId, instance in actuallyUsed.items():
            instanceTypes[instance["InstanceType"]] = instanceTypes.get(instance["InstanceType"],0)+1
            instancesByType[instance["InstanceType"]] = instancesByType.get(instance["InstanceType"],())+(instance,)

        for t in instancesByType:
            instancesByType[t] = list(instancesByType[t])

        with self.db.transaction():
            for state in State.lookupAll():
                if state.instance_type not in instanceTypes:
                    state.booted = 0

            for instType, count in instanceTypes.items():
                state = State.lookupAny(instance_type=instType)
                if not state:
                    state = State(instance_type=instType)
                state.booted = count

            for state in State.lookupAll():
                while state.booted > state.desired:
                    logging.info("We have %s instances of type %s booted vs %s desired. Shutting one down.", 
                        state.booted,
                        state.instance_type,
                        state.desired
                        )

                    instance = instancesByType[state.instance_type].pop()
                    self.api.terminateInstanceById(instance["InstanceId"])
                    state.booted -= 1

                while state.booted < state.desired:
                    logging.info("We have %s instances of type %s booted vs %s desired. Booting one.", 
                        state.booted,
                        state.instance_type,
                        state.desired
                        )

                    try:
                        self.api.bootWorker(state.instance_type)

                        state.booted += 1
                        state.capacityConstrained = False
                    except Exception as e:
                        if 'InsufficientInstanceCapacity' in str(e):
                            state.desired = state.booted
                            state.capacityConstrained = True
                        elif 'You have requested more instances ' in str(e):
                            maxCount = int(str(e).split('than your current instance limit of ')[1].split(' ')[0])
                            logging.info("Visible limit of %s observed for instance type %s", maxCount, state.instance_type)
                            state.observedLimit = maxCount
                            state.desired = min(state.desired, maxCount)
                        else:
                            logging.error("Failed to boot a worker:\n%s", traceback.format_exc())
                            time.sleep(self.SLEEP_INTERVAL)
                            break

        time.sleep(self.SLEEP_INTERVAL)
        

                        
