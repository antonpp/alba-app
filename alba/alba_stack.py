from aws_cdk import Stack, CfnOutput
from constructs import Construct

from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import RemovalPolicy


class AlbaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(self, 'HelloAlbaBucket', versioned=False, 
                           removal_policy=RemovalPolicy.DESTROY,
                           auto_delete_objects=True)

        pub_sn = ec2.SubnetConfiguration(
            name='hello-sn-config', 
            subnet_type=ec2.SubnetType.PUBLIC, 
            cidr_mask=24)

        vpc = ec2.Vpc(self, 
            'hello-alba-vpc', 
            cidr='10.0.0.0/16', 
            nat_gateways=1, 
            subnet_configuration=[pub_sn,])

        sg = ec2.SecurityGroup(self, 'hello-alba-sg', vpc=vpc, allow_all_outbound=True)
        sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "Allow ssh from anywhere")

        # TODO: add sagemaker.amazonaws.com as principal to trust relationships
        # by accessing assumeRolePolicy property...
        server_role = iam.Role(self, 'alba-server-role', 
                               assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
                               managed_policies=
                                   [iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess'),
                                    iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'),
                                    iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSageMakerFullAccess')]) 
        
        host = ec2.Instance(
            self,
            'alba-host',
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            role=server_role,
            security_group=sg,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.COMPUTE5, ec2.InstanceSize.XLARGE2),
            machine_image=ec2.AmazonLinuxImage(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
            key_name='macbook-ireland'
        )

        CfnOutput(self, id='host-ip', value=host.instance_public_ip, 
                  description="Public IP to alba app.", export_name='host-public-ip')
