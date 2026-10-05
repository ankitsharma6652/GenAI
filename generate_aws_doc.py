"""
Generate AWS Deployment Options Word Document
Covers: EC2, Lambda, ECS (EC2 + Fargate), EKS (Kubernetes)
"""

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import io, os, math

# ── Try to import matplotlib for diagrams ────────────────────────────────────
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("matplotlib not available — diagrams will be skipped")

# ── Color palette ────────────────────────────────────────────────────────────
AWS_ORANGE   = RGBColor(0xFF, 0x99, 0x00)
AWS_DARK     = RGBColor(0x23, 0x2F, 0x3E)
SECTION_BLUE = RGBColor(0x00, 0x63, 0xB1)
GREEN        = RGBColor(0x1D, 0x8A, 0x00)
RED          = RGBColor(0xC0, 0x00, 0x00)
GRAY         = RGBColor(0x60, 0x60, 0x60)
LIGHT_GRAY   = RGBColor(0xF2, 0xF2, 0xF2)
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)

# ── Hex helpers ───────────────────────────────────────────────────────────────
def hex2rgb(h): r=int(h[1:3],16); g=int(h[3:5],16); b=int(h[5:7],16); return (r/255,g/255,b/255)

# Colors for matplotlib diagrams
C = {
    'aws_bg':    '#232F3E',
    'aws_or':    '#FF9900',
    'vpc':       '#8B5CF6',
    'subnet_pub':'#D4EDDA',
    'subnet_pri':'#D1ECF1',
    'ec2':       '#FF9900',
    'alb':       '#17A2B8',
    'rds':       '#3B82F6',
    's3':        '#10B981',
    'lambda':    '#FF9900',
    'apigw':     '#EF4444',
    'ecs':       '#FF9900',
    'eks':       '#FF9900',
    'ecr':       '#6366F1',
    'fargate':   '#22C55E',
    'node':      '#F97316',
    'ingress':   '#EF4444',
    'box_bg':    '#FEFEFE',
    'shadow':    '#E5E7EB',
    'text_dark': '#1F2937',
    'text_mid':  '#374151',
    'internet':  '#6B7280',
}

# ─────────────────────────────────────────────────────────────────────────────
# DIAGRAM GENERATORS
# ─────────────────────────────────────────────────────────────────────────────
def arrow(ax, x1,y1,x2,y2,color='#374151',lw=1.5,style='->'):
    ax.annotate('',xy=(x2,y2),xytext=(x1,y1),
        arrowprops=dict(arrowstyle=style,color=color,lw=lw,
                        connectionstyle='arc3,rad=0.05'))

def box(ax,x,y,w,h,text,bg='#FEFEFE',border='#374151',
        fontsize=8,bold=False,text_color='#1F2937',radius=0.3,
        subtext=None):
    fancy = FancyBboxPatch((x-w/2,y-h/2),w,h,
        boxstyle=f"round,pad=0.1,rounding_size={radius}",
        facecolor=bg,edgecolor=border,linewidth=1.5,zorder=3)
    ax.add_patch(fancy)
    kwargs = dict(ha='center',va='center',fontsize=fontsize,
                  color=text_color,zorder=4,
                  fontweight='bold' if bold else 'normal')
    if subtext:
        ax.text(x,y+h*0.12,text,**kwargs)
        ax.text(x,y-h*0.22,subtext,ha='center',va='center',
                fontsize=fontsize-1,color='#6B7280',zorder=4)
    else:
        ax.text(x,y,text,**kwargs)

def cloud_box(ax,x,y,w,h,label,bg='#F3F4F6',border='#9CA3AF',fontsize=7.5):
    """Dashed box to represent cloud/VPC boundary"""
    rect = mpatches.FancyBboxPatch((x,y),w,h,
        boxstyle="round,pad=0.05",
        facecolor=bg,edgecolor=border,linewidth=1.5,
        linestyle='--',zorder=1)
    ax.add_patch(rect)
    ax.text(x+0.12,y+h-0.18,label,fontsize=fontsize,
            color=border,fontweight='bold',zorder=2)

def save_fig(fig, label):
    buf = io.BytesIO()
    fig.savefig(buf,format='png',dpi=150,bbox_inches='tight',
                facecolor='white',edgecolor='none')
    buf.seek(0)
    plt.close(fig)
    return buf

# ── Diagram 1: EC2 ────────────────────────────────────────────────────────────
def make_ec2_diagram():
    fig,ax = plt.subplots(figsize=(10,6))
    ax.set_xlim(0,10); ax.set_ylim(0,6); ax.axis('off')
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    # Title
    ax.text(5,5.7,'EC2 Deployment Architecture',ha='center',
            fontsize=12,fontweight='bold',color=C['text_dark'])

    # Internet
    box(ax,5,5.1,1.8,0.55,'🌐 Internet',bg='#E5E7EB',border=C['internet'],
        fontsize=8,bold=True,text_color='#374151')

    # AWS VPC box
    cloud_box(ax,0.3,0.3,9.4,4.5,'AWS VPC  (10.0.0.0/16)',bg='#FFF9F0',border='#F59E0B')

    # Public Subnet
    cloud_box(ax,0.6,0.6,4.1,3.6,'Public Subnet (10.0.1.0/24)',bg='#D4EDDA',border='#28A745',fontsize=7)
    # Private Subnet
    cloud_box(ax,5.2,0.6,4.2,3.6,'Private Subnet (10.0.2.0/24)',bg='#D1ECF1',border='#17A2B8',fontsize=7)

    # ALB
    box(ax,2.7,3.5,2.8,0.6,'⚖️ Application Load Balancer',
        bg='#DBEAFE',border=C['alb'],fontsize=7.5,bold=True,text_color='#1E40AF')
    # Internet Gateway
    box(ax,2.7,4.4,2.4,0.5,'🔀 Internet Gateway',
        bg='#FEF3C7',border='#D97706',fontsize=7.5,text_color='#92400E')

    # EC2 Instances
    for i,(xi,lbl) in enumerate([(5.8,'EC2 Instance 1'),(7.1,'EC2 Instance 2'),(8.4,'EC2 Instance 3')]):
        box(ax,xi,2.8,1.0,0.65,f'🖥\n{lbl}',bg='#FFF7ED',border=C['ec2'],
            fontsize=6.5,text_color='#92400E')
    ax.text(7.1,2.35,'(Auto Scaling Group)',ha='center',fontsize=6.5,color='#6B7280')

    # RDS
    box(ax,7.1,1.3,2.4,0.7,'🗄️ Amazon RDS\n(Multi-AZ)',
        bg='#EFF6FF',border=C['rds'],fontsize=7,text_color='#1E40AF')

    # IAM Role
    box(ax,1.3,1.5,1.4,0.6,'🔐 IAM\nRole',bg='#F0FDF4',border='#16A34A',fontsize=7,text_color='#166534')
    # S3
    box(ax,2.7,1.5,1.5,0.6,'📦 S3\nBucket',bg='#F0FDF4',border=C['s3'],fontsize=7,text_color='#065F46')

    # CloudWatch
    box(ax,1.3,2.7,1.4,0.6,'📊 Cloud\nWatch',bg='#FFF7ED',border='#D97706',fontsize=7,text_color='#92400E')

    # AMI label
    box(ax,2.0,0.85,2.0,0.5,'💿 AMI (App+OS Image)',bg='#FAFAFA',border='#9CA3AF',fontsize=6.5,text_color='#374151')

    # Arrows
    arrow(ax,5,5.1-0.28,5,4.4+0.25)           # Internet → IGW
    arrow(ax,2.7,4.4-0.25,2.7,3.5+0.3)        # IGW → ALB
    arrow(ax,4.1,3.5,5.5,3.0)                 # ALB → EC2-1
    arrow(ax,4.1,3.5,7.1,3.0)                 # ALB → EC2-2
    arrow(ax,4.1,3.5,8.4,3.0)                 # ALB → EC2-3
    arrow(ax,7.1,2.45,7.1,1.65)               # EC2 → RDS
    arrow(ax,3.2,1.5,4.7,2.1,style='->')      # S3 → context

    ax.text(5,0.12,'User deploys via: SSH → AMI → Launch Template → Auto Scaling → ALB',
            ha='center',fontsize=7,color='#6B7280',style='italic')

    return save_fig(fig,'ec2')

# ── Diagram 2: Lambda ─────────────────────────────────────────────────────────
def make_lambda_diagram():
    fig,ax = plt.subplots(figsize=(10,5.5))
    ax.set_xlim(0,10); ax.set_ylim(0,5.5); ax.axis('off')
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')

    ax.text(5,5.2,'AWS Lambda (Serverless) Deployment Architecture',
            ha='center',fontsize=12,fontweight='bold',color=C['text_dark'])

    # Triggers row
    triggers = [
        ('🌐\nAPI Gateway\n(REST/HTTP)',1.0,'#DBEAFE','#1E40AF'),
        ('📅\nEventBridge\n(Scheduler)',2.8,'#F0FDF4','#166534'),
        ('📥\nS3 Event\n(Upload)',4.6,'#FFF7ED','#92400E'),
        ('📬\nSQS/SNS\nQueue',6.4,'#EDE9FE','#5B21B6'),
        ('🔄\nKinesis\nStream',8.2,'#ECFDF5','#065F46'),
    ]
    ax.text(5,4.65,'Event Triggers',ha='center',fontsize=8.5,
            fontweight='bold',color='#6B7280')
    for (lbl,x,bg,border) in triggers:
        box(ax,x,4.1,1.55,0.85,lbl,bg=bg,border=border,fontsize=6.5,text_color=border)

    # Lambda Function box (central)
    cloud_box(ax,2.5,2.1,5.0,1.45,'Lambda Execution Environment',bg='#FFF9F0',border='#F59E0B')
    box(ax,5,2.75,4.2,0.9,'⚡ Lambda Function\n(Python / Node / Java / Go)',
        bg='#FEF3C7',border=C['aws_or'],fontsize=8.5,bold=True,text_color='#92400E')
    ax.text(5,2.25,'Runtime Container (Managed by AWS)',ha='center',fontsize=6.5,color='#6B7280')

    # Downstream
    downstream = [
        ('🗄️\nDynamoDB',1.5,0.9,'#EFF6FF','#1D4ED8'),
        ('📦\nS3 Bucket',3.2,0.9,'#F0FDF4','#166534'),
        ('🗃️\nRDS (VPC)',5.0,0.9,'#EFF6FF','#1D4ED8'),
        ('📧\nSNS/SES',6.8,0.9,'#EDE9FE','#5B21B6'),
        ('📊\nCloudWatch\nLogs',8.5,0.9,'#FFF7ED','#92400E'),
    ]
    ax.text(5,1.55,'Downstream Integrations',ha='center',fontsize=8.5,
            fontweight='bold',color='#6B7280')
    for (lbl,x,y,bg,border) in downstream:
        box(ax,x,y,1.4,0.85,lbl,bg=bg,border=border,fontsize=6.5,text_color=border)

    # Arrows triggers → Lambda
    for (_,x,_bg,_b) in triggers:
        arrow(ax,x,4.1-0.42,x,3.8,style='->')
        ax.annotate('',xy=(5,2.75+0.45),xytext=(x,3.6),
            arrowprops=dict(arrowstyle='->',color='#9CA3AF',lw=1.2,
                            connectionstyle='arc3,rad=0.1'))

    # Lambda → downstream
    for (lbl,x,y,bg,border) in downstream:
        arrow(ax,5,2.75-0.45,x,y+0.43)

    ax.text(5,0.15,'Concurrency: 0 → 1000s of instances in milliseconds. No server management.',
            ha='center',fontsize=7,color='#6B7280',style='italic')

    return save_fig(fig,'lambda')

# ── Diagram 3: ECS ────────────────────────────────────────────────────────────
def make_ecs_diagram():
    fig,(ax1,ax2) = plt.subplots(1,2,figsize=(14,6))
    fig.patch.set_facecolor('white')

    for ax in [ax1,ax2]:
        ax.set_xlim(0,7); ax.set_ylim(0,6); ax.axis('off')
        ax.set_facecolor('white')

    # ── Left: ECS on EC2 ─────────────────────────────────────────────────────
    ax1.text(3.5,5.7,'ECS on EC2 Launch Type',ha='center',
             fontsize=11,fontweight='bold',color=C['text_dark'])
    ax1.text(3.5,5.4,'(You manage EC2 instances)',ha='center',
             fontsize=8,color='#6B7280',style='italic')

    cloud_box(ax1,0.2,0.2,6.6,5.0,'AWS VPC',bg='#FFF9F0',border='#F59E0B',fontsize=7.5)

    # ECS Cluster
    cloud_box(ax1,0.5,0.5,6.0,4.0,'ECS Cluster',bg='#F9FAFB',border='#6B7280',fontsize=7)

    # EC2 Node boxes
    for i,(xi,lbl) in enumerate([(1.3,'EC2 Node A'),(3.5,'EC2 Node B'),(5.7,'EC2 Node C')]):
        cloud_box(ax1,xi-0.8,0.8,1.6,3.0,lbl,bg='#FFF3E0',border=C['node'],fontsize=6.5)
        # Containers in each node
        for j,cy in enumerate([1.3,2.15,3.0]):
            box(ax1,xi,cy,1.2,0.6,f'📦 Container\nTask {i*3+j+1}',
                bg='#DBEAFE',border='#2563EB',fontsize=5.5,text_color='#1D4ED8')

    # ALB
    box(ax1,3.5,4.85,3.0,0.55,'⚖️ ALB',bg='#DBEAFE',border=C['alb'],
        fontsize=7.5,bold=True,text_color='#1E40AF')

    # ECR
    box(ax1,1.0,4.85,1.8,0.55,'📷 Amazon ECR\n(Container Registry)',
        bg='#EDE9FE',border=C['ecr'],fontsize=6,text_color='#5B21B6')

    arrow(ax1,3.5,4.85-0.28,3.5,3.85)
    ax1.text(3.5,0.35,'ECS Agent on each EC2. You patch/manage nodes.',
             ha='center',fontsize=6.5,color='#6B7280',style='italic')

    # ── Right: ECS Fargate ───────────────────────────────────────────────────
    ax2.text(3.5,5.7,'ECS on AWS Fargate',ha='center',
             fontsize=11,fontweight='bold',color=C['text_dark'])
    ax2.text(3.5,5.4,'(AWS manages infra — serverless containers)',ha='center',
             fontsize=8,color='#6B7280',style='italic')

    cloud_box(ax2,0.2,0.2,6.6,5.0,'AWS VPC',bg='#FFF9F0',border='#F59E0B',fontsize=7.5)
    cloud_box(ax2,0.5,0.5,6.0,4.0,'ECS Cluster (Fargate)',bg='#F0FDF4',border='#16A34A',fontsize=7)

    # Fargate tasks (no node wrapper)
    task_positions = [(1.2,3.2),(3.5,3.2),(5.8,3.2),
                      (1.2,2.0),(3.5,2.0),(5.8,2.0),
                      (2.35,0.9),(4.65,0.9)]
    for i,(xi,yi) in enumerate(task_positions):
        box(ax2,xi,yi,1.55,0.8,f'📦 Fargate Task {i+1}\n(micro-VM isolated)',
            bg='#ECFDF5',border=C['fargate'],fontsize=5.8,text_color='#065F46')

    # AWS Fargate label
    box(ax2,3.5,1.4,5.5,0.45,'⚡ AWS Fargate Managed Infrastructure (Invisible to you)',
        bg='#D1FAE5',border='#059669',fontsize=6.5,bold=True,text_color='#065F46')

    # ALB
    box(ax2,3.5,4.85,3.0,0.55,'⚖️ ALB',bg='#DBEAFE',border=C['alb'],
        fontsize=7.5,bold=True,text_color='#1E40AF')
    # ECR
    box(ax2,1.0,4.85,1.8,0.55,'📷 Amazon ECR',
        bg='#EDE9FE',border=C['ecr'],fontsize=6.5,text_color='#5B21B6')

    arrow(ax2,3.5,4.85-0.28,3.5,3.6)
    ax2.text(3.5,0.35,'No EC2 to manage. AWS provisions & patches compute.',
             ha='center',fontsize=6.5,color='#6B7280',style='italic')

    plt.tight_layout(pad=0.5)
    return save_fig(fig,'ecs')

# ── Diagram 4: EKS ────────────────────────────────────────────────────────────
def make_eks_diagram():
    fig,ax = plt.subplots(figsize=(12,7))
    ax.set_xlim(0,12); ax.set_ylim(0,7); ax.axis('off')
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')

    ax.text(6,6.7,'Amazon EKS (Kubernetes) Deployment Architecture',
            ha='center',fontsize=12,fontweight='bold',color=C['text_dark'])

    # AWS cloud boundary
    cloud_box(ax,0.2,0.2,11.6,6.2,'AWS Cloud',bg='#FFF9F0',border='#F59E0B',fontsize=8)

    # EKS Control Plane (managed)
    cloud_box(ax,0.5,4.8,11.0,1.3,'EKS Managed Control Plane (AWS manages — HA across 3 AZs)',
              bg='#EDE9FE',border='#7C3AED',fontsize=7.5)
    cp_items = [
        (1.8,5.35,'API Server'),
        (3.6,5.35,'etcd'),
        (5.4,5.35,'Scheduler'),
        (7.2,5.35,'Controller\nManager'),
        (9.0,5.35,'Cloud\nController'),
        (10.8,5.35,'CoreDNS'),
    ]
    for x,y,lbl in cp_items:
        box(ax,x,y,1.55,0.6,lbl,bg='#EDE9FE',border='#7C3AED',
            fontsize=6.5,text_color='#5B21B6')

    # VPC
    cloud_box(ax,0.5,0.3,11.0,4.3,'VPC  (10.0.0.0/16)',bg='#F9FAFB',border='#6B7280',fontsize=7)

    # Worker Nodes (Node Group)
    for ni,(nx,ncolor,nlabel) in enumerate([
        (1.3,'#FFF3E0','Node Group 1\n(m5.xlarge × 3)'),
        (5.0,'#FFF3E0','Node Group 2\n(g4dn.xlarge × 2)'),
        (8.7,'#E0F2FE','Fargate Profile\n(Serverless nodes)')
    ]):
        cloud_box(ax,nx-0.8,0.6,3.2,3.3,nlabel,bg=ncolor,
                  border=C['node'] if ni<2 else C['fargate'],fontsize=6.5)
        # Pods inside node
        pods = [
            (nx-0.35,2.8,'App Pod','#DBEAFE','#1D4ED8'),
            (nx+0.45,2.8,'App Pod','#DBEAFE','#1D4ED8'),
            (nx-0.35,2.0,'Sidecar\n(Envoy)','#FEF3C7','#92400E'),
            (nx+0.45,2.0,'DaemonSet\n(FluentD)','#F0FDF4','#166534'),
            (nx,1.3,'System Pod\n(CoreDNS)','#EDE9FE','#5B21B6'),
        ]
        for px,py,plbl,pbg,pb in pods:
            box(ax,px,py,0.82,0.65,plbl,bg=pbg,border=pb,fontsize=5.2,text_color=pb)

    # Ingress / ALB
    box(ax,2.7,4.45,3.0,0.55,'⚖️ AWS Load Balancer\nController (Ingress)',
        bg='#DBEAFE',border=C['alb'],fontsize=6.5,bold=True,text_color='#1E40AF')
    # ECR
    box(ax,6.0,4.45,2.2,0.55,'📷 Amazon ECR',
        bg='#EDE9FE',border=C['ecr'],fontsize=7,text_color='#5B21B6')
    # IAM / IRSA
    box(ax,8.5,4.45,2.8,0.55,'🔐 IRSA (IAM Roles\nfor Service Accounts)',
        bg='#F0FDF4',border='#16A34A',fontsize=6.5,text_color='#166534')

    # Kubectl user
    box(ax,10.8,6.2,1.5,0.5,'👤 kubectl\n/ Helm',bg='#F9FAFB',border='#6B7280',fontsize=6.5,text_color='#374151')
    arrow(ax,10.8,6.2-0.25,9.0,5.35+0.3)

    # Internet → Ingress
    box(ax,1.0,6.2,1.5,0.5,'🌐 Internet\nTraffic',bg='#E5E7EB',border='#6B7280',fontsize=6.5)
    arrow(ax,1.0,6.2-0.25,2.7,4.45+0.28)

    # Ingress → pods
    arrow(ax,2.7,4.45-0.28,1.3,3.1)
    arrow(ax,2.7,4.45-0.28,5.0,3.1)

    ax.text(6,0.15,'kubectl apply -f deployment.yaml | helm install | Karpenter autoscaling',
            ha='center',fontsize=7,color='#6B7280',style='italic')

    return save_fig(fig,'eks')

# ── Diagram 5: Comparison ─────────────────────────────────────────────────────
def make_comparison_diagram():
    fig,ax = plt.subplots(figsize=(12,5))
    ax.set_xlim(0,12); ax.set_ylim(0,5); ax.axis('off')
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')

    ax.text(6,4.75,'AWS Deployment Options — Decision Matrix',
            ha='center',fontsize=12,fontweight='bold',color=C['text_dark'])

    options = [
        ('EC2','#FF9900','#FFF7ED','#92400E',1.5),
        ('ECS/EC2','#17A2B8','#E0F2FE','#0E7490',3.8),
        ('ECS/Fargate','#22C55E','#DCFCE7','#15803D',6.1),
        ('EKS','#8B5CF6','#EDE9FE','#5B21B6',8.4),
    ]

    criteria = ['Infra\nControl','Ops\nOverhead','Scalability','Cost\nEfficiency','Portability','Best For']
    values = {
        'EC2':         ['●●●●●','●●●●●','●●●○○','●●○○○','●●○○○','Long-running,\nstateful apps'],
        'ECS/EC2':     ['●●●●○','●●●○○','●●●●○','●●●○○','●●●○○','Containerized\nmicroservices'],
        'ECS/Fargate': ['●●○○○','●●○○○','●●●●●','●●●●○','●●●●○','Serverless\ncontainers'],
        'EKS':         ['●●●●●','●●○○○','●●●●●','●●●○○','●●●●●','Complex\norchestration'],
    }
    colors_map = {'●●●●●':'#16A34A','●●●●○':'#65A30D','●●●○○':'#CA8A04','●●○○○':'#DC2626','●○○○○':'#DC2626'}

    col_w = 1.9; row_h = 0.52; start_x = 2.3; start_y = 3.9

    # Headers: criteria
    ax.text(1.1,start_y+0.25,'Criterion',ha='center',fontsize=8,fontweight='bold',color='#374151')
    for i,(opt,hborder,hbg,htxt,cx) in enumerate(options):
        box(ax,cx,start_y+0.25,col_w-0.15,0.45,opt,bg=hbg,border=hborder,
            fontsize=9,bold=True,text_color=htxt)

    # Rows
    for ri,crit in enumerate(criteria):
        y = start_y - (ri+1)*row_h
        bg = '#F9FAFB' if ri%2==0 else 'white'
        ax.add_patch(mpatches.Rectangle((0,y-row_h/2),12,row_h,
                                         facecolor=bg,edgecolor='none',zorder=0))
        ax.text(1.1,y,crit,ha='center',va='center',fontsize=7.5,
                color='#374151',fontweight='bold')
        for (opt,hborder,hbg,htxt,cx) in options:
            val = values[opt][ri]
            c = colors_map.get(val,'#374151')
            ax.text(cx,y,val,ha='center',va='center',fontsize=8,color=c,fontweight='bold')

    # Divider line
    ax.plot([0,12],[start_y+0.02,start_y+0.02],color='#D1D5DB',linewidth=1)

    ax.text(6,0.2,
        '● = High   ○ = Low   |   Recommendation: Start with Fargate → Graduate to EKS for complexity',
        ha='center',fontsize=7.5,color='#6B7280',style='italic')

    return save_fig(fig,'compare')

# ── Diagram 6: Decision Flowchart ─────────────────────────────────────────────
def make_decision_diagram():
    fig,ax = plt.subplots(figsize=(10,7))
    ax.set_xlim(0,10); ax.set_ylim(0,7); ax.axis('off')
    ax.set_facecolor('white'); fig.patch.set_facecolor('white')

    ax.text(5,6.75,'AWS Deployment Option — Decision Flowchart',
            ha='center',fontsize=11,fontweight='bold',color=C['text_dark'])

    def diamond(ax,x,y,w,h,text,color='#1E40AF',bg='#DBEAFE'):
        pts = [(x,y+h/2),(x+w/2,y),(x,y-h/2),(x-w/2,y)]
        patch = mpatches.Polygon(pts,closed=True,facecolor=bg,edgecolor=color,linewidth=1.8,zorder=3)
        ax.add_patch(patch)
        ax.text(x,y,text,ha='center',va='center',fontsize=7,color=color,fontweight='bold',zorder=4)

    def result(ax,x,y,text,color,bg):
        box(ax,x,y,2.0,0.65,text,bg=bg,border=color,fontsize=7.5,bold=True,text_color=color)

    # Start
    box(ax,5,6.3,2.5,0.5,'🚀 Deploy Application',bg='#232F3E',border='#FF9900',
        fontsize=8.5,bold=True,text_color='#FF9900')

    # Q1
    diamond(ax,5,5.4,3.2,0.9,'Is your app\ncontainerized?')
    arrow(ax,5,6.3-0.25,5,5.4+0.45)

    # NO → EC2
    ax.text(1.9,5.4,'NO',ha='center',fontsize=7.5,color='#DC2626',fontweight='bold')
    arrow(ax,5-1.6,5.4,2.2,5.4,style='->',color='#DC2626')
    result(ax,1.2,5.4,'🖥 Use EC2\n(VMs + AMI)','#92400E','#FFF7ED')

    # YES → Q2
    ax.text(5.2,4.75,'YES',ha='center',fontsize=7.5,color='#16A34A',fontweight='bold')
    diamond(ax,5,4.0,3.5,0.9,'Need full K8s features?\n(RBAC, CRDs, Helm, mesh)')
    arrow(ax,5,5.4-0.45,5,4.0+0.45)

    # YES → EKS
    arrow(ax,5+1.75,4.0,7.9,4.0,style='->',color='#16A34A')
    ax.text(7.1,4.15,'YES',ha='center',fontsize=7.5,color='#16A34A',fontweight='bold')
    result(ax,8.8,4.0,'☸ Use EKS\n(Kubernetes)','#5B21B6','#EDE9FE')

    # NO → Q3
    ax.text(4.8,3.3,'NO',ha='center',fontsize=7.5,color='#DC2626',fontweight='bold')
    diamond(ax,5,2.5,3.5,0.9,'Need to control\nEC2 instance type/GPU?')
    arrow(ax,5,4.0-0.45,5,2.5+0.45)

    # YES → ECS EC2
    arrow(ax,5+1.75,2.5,7.9,2.5,style='->',color='#16A34A')
    ax.text(7.1,2.65,'YES',ha='center',fontsize=7.5,color='#16A34A',fontweight='bold')
    result(ax,8.8,2.5,'📦 ECS on EC2\n(EC2 Launch Type)','#0E7490','#E0F2FE')

    # NO → Q4
    ax.text(4.8,1.8,'NO',ha='center',fontsize=7.5,color='#DC2626',fontweight='bold')
    diamond(ax,5,1.2,3.5,0.9,'Event-driven or\nshort-lived function?')
    arrow(ax,5,2.5-0.45,5,1.2+0.45)

    # YES → Lambda
    arrow(ax,5+1.75,1.2,7.9,1.2,style='->',color='#16A34A')
    ax.text(7.1,1.35,'YES',ha='center',fontsize=7.5,color='#16A34A',fontweight='bold')
    result(ax,8.8,1.2,'⚡ Use Lambda\n(Serverless fn)','#92400E','#FFF7ED')

    # NO → Fargate
    ax.text(3.5,0.5,'NO → Long-running container, zero ops overhead',
            ha='center',fontsize=7,color='#15803D')
    arrow(ax,5,1.2-0.45,5,0.65)
    result(ax,5,0.35,'🚀 ECS Fargate\n(Serverless containers)','#15803D','#DCFCE7')

    return save_fig(fig,'decision')

# ─────────────────────────────────────────────────────────────────────────────
# DOCUMENT BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def set_col_width(col, width):
    col.width = width

def add_heading(doc, text, level=1, color=None):
    h = doc.add_heading(text, level=level)
    if color and h.runs:
        h.runs[0].font.color.rgb = color
    return h

def add_para(doc, text, indent=False, bold_start=None, color=None):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Inches(0.3)
    if bold_start:
        run = p.add_run(bold_start)
        run.bold = True
        if color:
            run.font.color.rgb = color
        p.add_run(text)
    else:
        run = p.add_run(text)
        if color:
            run.font.color.rgb = color
    p.paragraph_format.space_after = Pt(4)
    return p

def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(text)
    p.paragraph_format.left_indent = Inches(0.3 + level * 0.25)
    p.paragraph_format.space_after = Pt(2)

def shade_cell(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color.lstrip('#'))
    tcPr.append(shd)

def cell_text(cell, text, bold=False, color=None, fontsize=9, align='left'):
    cell.text = ''
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if align=='center' else WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    run.font.size = Pt(fontsize)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

def add_image_buf(doc, buf, width_inches=6.0, caption=None):
    doc.add_picture(buf, width=Inches(width_inches))
    last = doc.paragraphs[-1]
    last.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if caption:
        cp = doc.add_paragraph(caption)
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.runs[0].font.italic = True
        cp.runs[0].font.size = Pt(8.5)
        cp.runs[0].font.color.rgb = GRAY
        cp.paragraph_format.space_after = Pt(10)

def add_code_block(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.4)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x07, 0x36, 0x42)

def add_separator(doc):
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

def build_document():
    doc = Document()

    # ── Page setup ───────────────────────────────────────────────────────────
    section = doc.sections[0]
    section.page_width  = Inches(8.5)
    section.page_height = Inches(11)
    section.left_margin   = Inches(1.0)
    section.right_margin  = Inches(1.0)
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.0)

    # Normal style
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(10.5)

    # ─────────────────────────────────────────────────────────────────────────
    # TITLE PAGE
    # ─────────────────────────────────────────────────────────────────────────
    doc.add_paragraph()
    doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tr = title.add_run('AWS Application Deployment Options')
    tr.font.size = Pt(28)
    tr.font.bold = True
    tr.font.color.rgb = AWS_ORANGE

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = sub.add_run('EC2  ·  Lambda  ·  ECS (EC2 & Fargate)  ·  EKS (Kubernetes)')
    sr.font.size = Pt(16)
    sr.font.color.rgb = AWS_DARK
    sr.font.bold = True

    doc.add_paragraph()
    sub2 = doc.add_paragraph()
    sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub2.add_run('A Practical Guide with Architecture Diagrams\nfor Deploying ML and General Applications on AWS').font.size = Pt(12)

    doc.add_paragraph()
    doc.add_paragraph()
    doc.add_paragraph()

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    metarun = meta.add_run(
        'Document prepared for: Engineering / ML Teams\n'
        'Cloud Provider: Amazon Web Services (AWS)\n'
        'Scope: EC2 · AWS Lambda · Amazon ECS · Amazon EKS\n'
    )
    metarun.font.size = Pt(10.5)
    metarun.font.color.rgb = GRAY
    metarun.font.italic = True

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # TABLE OF CONTENTS (manual)
    # ─────────────────────────────────────────────────────────────────────────
    add_heading(doc, 'Table of Contents', level=1, color=AWS_DARK)
    toc_items = [
        ('1.', 'Introduction & Overview', 3),
        ('2.', 'EC2 Deployment', 3),
        ('   2.1', 'Architecture', 4),
        ('   2.2', 'Deployment Steps', 5),
        ('   2.3', 'Practical ML Scenario', 5),
        ('   2.4', 'Pros & Cons', 6),
        ('3.', 'AWS Lambda Deployment', 6),
        ('   3.1', 'Architecture', 7),
        ('   3.2', 'Deployment Steps', 7),
        ('   3.3', 'Practical ML Scenario', 8),
        ('   3.4', 'Pros & Cons', 8),
        ('4.', 'ECS — EC2 Launch Type vs Fargate', 9),
        ('   4.1', 'What is ECS?', 9),
        ('   4.2', 'EC2 Launch Type vs Fargate Explained', 9),
        ('   4.3', 'Architecture', 10),
        ('   4.4', 'Deployment Steps', 10),
        ('   4.5', 'Practical ML Scenario', 11),
        ('   4.6', 'Pros & Cons', 11),
        ('5.', 'Amazon EKS (Kubernetes) Deployment', 12),
        ('   5.1', 'Architecture', 12),
        ('   5.2', 'Deployment Steps', 13),
        ('   5.3', 'Practical ML Scenario', 13),
        ('   5.4', 'Pros & Cons', 14),
        ('6.', 'Side-by-Side Comparison', 14),
        ('7.', 'Decision Guide — When to Choose Which', 16),
        ('8.', 'Cost Comparison & Pricing Model', 17),
        ('9.', 'Summary & Recommendations', 18),
    ]
    for num, item, pg in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        tab_leader = p.add_run(f'{num}  {item}')
        tab_leader.font.size = Pt(10)
        if not num.startswith('   '):
            tab_leader.font.bold = True

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 1: INTRODUCTION
    # ─────────────────────────────────────────────────────────────────────────
    add_heading(doc, '1. Introduction & Overview', level=1, color=AWS_ORANGE)
    add_para(doc,
        'Amazon Web Services (AWS) offers multiple ways to deploy applications — from traditional '
        'virtual machines to fully managed serverless platforms. Choosing the right deployment model '
        'is one of the most critical architectural decisions, directly impacting cost, scalability, '
        'operational complexity, and performance.\n\n'
        'This document covers four primary AWS deployment strategies with a focus on practical '
        'ML/AI applications (e.g., a FastAPI model serving endpoint, a batch inference job, '
        'or a real-time prediction pipeline):')
    options_intro = [
        ('🖥  EC2 (Elastic Compute Cloud)',
         'Full virtual machines — you control the OS, runtime, and configuration. Best for '
         'workloads requiring maximum control, GPU instances, or legacy applications.'),
        ('⚡  AWS Lambda',
         'Serverless functions — event-driven, zero infrastructure management. Ideal for '
         'lightweight inference endpoints, ETL triggers, or preprocessing jobs.'),
        ('📦  Amazon ECS (Elastic Container Service)',
         'Managed Docker container orchestration. Two flavors: '
         '(a) EC2 launch type — you manage EC2 workers; '
         '(b) Fargate — AWS manages compute, you only think about containers.'),
        ('☸  Amazon EKS (Elastic Kubernetes Service)',
         'Fully managed Kubernetes control plane on AWS. Best for teams already using K8s '
         'or needing advanced orchestration (Helm, CRDs, service meshes, Karpenter autoscaling).'),
    ]
    for title_opt, desc in options_intro:
        p = doc.add_paragraph()
        run = p.add_run(title_opt)
        run.bold = True
        run.font.color.rgb = SECTION_BLUE
        p.add_run(f'\n    {desc}')
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(5)

    add_para(doc,
        'Throughout this document, we use a consistent practical scenario: '
        'deploying an ML inference API (FastAPI + PyTorch model) that serves real-time predictions '
        'with the example input/output: POST /predict → JSON response with model scores.')

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 2: EC2
    # ─────────────────────────────────────────────────────────────────────────
    add_heading(doc, '2. EC2 Deployment', level=1, color=AWS_ORANGE)

    add_heading(doc, '2.1  What is EC2?', level=2, color=SECTION_BLUE)
    add_para(doc,
        'Amazon EC2 (Elastic Compute Cloud) provides resizable virtual machines in the AWS cloud. '
        'You have complete control over the operating system, networking configuration, storage, '
        'and software stack. EC2 is the foundation of most other AWS compute services.')

    add_heading(doc, '2.2  Architecture', level=2, color=SECTION_BLUE)
    add_para(doc,
        'A production-grade EC2 deployment for an ML API follows this architecture:')
    arch_bullets = [
        'Internet Gateway → Routes external traffic into the VPC',
        'Application Load Balancer (ALB) → Distributes traffic across multiple EC2 instances',
        'Auto Scaling Group → Automatically adds/removes EC2 instances based on CPU/memory metrics',
        'EC2 Instances (Private Subnet) → Run your ML API (FastAPI + Uvicorn + PyTorch)',
        'Amazon RDS → Managed database for logging predictions and user data',
        'Amazon S3 → Stores model weights, logs, and artifacts',
        'IAM Role → Grants EC2 instances secure access to S3, RDS, and other AWS services',
        'CloudWatch → Collects metrics, logs, and triggers Auto Scaling alarms',
    ]
    for b in arch_bullets:
        add_bullet(doc, b)

    if HAS_MPL:
        add_separator(doc)
        buf = make_ec2_diagram()
        add_image_buf(doc, buf, 6.2,
                      'Figure 1: EC2 Deployment Architecture — ALB + Auto Scaling Group + RDS + S3')
    add_separator(doc)

    add_heading(doc, '2.3  Deployment Steps', level=2, color=SECTION_BLUE)
    steps = [
        ('Step 1: Prepare Your AMI (Amazon Machine Image)',
         'Launch a base EC2 instance (e.g., Ubuntu 22.04 on m5.xlarge or g4dn.xlarge for GPU). '
         'Install your runtime: Python 3.10, PyTorch, FastAPI, Uvicorn, and your model weights. '
         'Create an AMI snapshot from this instance for reproducible deployments.'),
        ('Step 2: Create a Launch Template',
         'Define: instance type, AMI ID, security groups, IAM instance profile, EBS volume size, '
         'and UserData script that starts your FastAPI application on boot.'),
        ('Step 3: Configure Auto Scaling Group',
         'Set min=2, max=10, desired=3 instances across multiple Availability Zones. '
         'Define scaling policies: scale out when CPU > 70%, scale in when CPU < 30%.'),
        ('Step 4: Create Application Load Balancer (ALB)',
         'Create target group pointing to EC2 instances on port 8000. '
         'Configure health checks at /health endpoint. ALB handles HTTPS termination.'),
        ('Step 5: Set Up CI/CD Pipeline',
         'Use AWS CodePipeline: on git push → CodeBuild bakes new AMI → CodeDeploy rolls out '
         'to ASG using blue/green or rolling deployment strategy.'),
        ('Step 6: Configure CloudWatch Monitoring',
         'Create dashboards for CPU, memory, request latency, and error rate. '
         'Set up alarms to trigger Auto Scaling and send SNS alerts on anomalies.'),
    ]
    for title_step, desc in steps:
        p = doc.add_paragraph()
        p.add_run(title_step).bold = True
        p.paragraph_format.space_before = Pt(6)
        add_para(doc, desc, indent=True)

    add_heading(doc, '2.4  Practical ML Scenario', level=2, color=SECTION_BLUE)
    add_para(doc,
        'Scenario: Deploying a PyTorch BERT text classification model as a FastAPI service '
        'handling 500 requests/second with < 100ms p99 latency.\n')
    scenario_items = [
        'Instance Type: c5.4xlarge (16 vCPU, 32 GB RAM) or g4dn.xlarge (1× NVIDIA T4 GPU)',
        'Model Loading: Model weights stored in S3 → downloaded to /tmp at instance startup',
        'Scaling: ASG scales from 3 to 15 instances based on ALB request count',
        'Cost: ~$0.68/hr per c5.4xlarge × 3 instances = $2.04/hr (on-demand), or use Spot to save 70%',
        'Latency: ~35ms per inference request at p50, ~80ms at p99',
        'Deployment: Blue/Green with CodeDeploy — zero downtime during model updates',
    ]
    for item in scenario_items:
        add_bullet(doc, item)

    add_para(doc, 'Sample UserData bootstrap script:', indent=False)
    add_code_block(doc,
        '#!/bin/bash\n'
        'cd /app && source venv/bin/activate\n'
        'aws s3 cp s3://my-models/bert-classifier.pt /app/models/\n'
        'uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 &')

    add_heading(doc, '2.5  EC2 Pros and Cons', level=2, color=SECTION_BLUE)
    pros = ['Full control over OS, networking, runtime versions',
            'Supports GPU instances (g4dn, p3, p4d) for deep learning',
            'Ideal for long-running stateful services',
            'Spot Instances can reduce cost by up to 90%',
            'Easy migration of on-premise workloads']
    cons = ['You manage patching, OS updates, and scaling logic',
            'Slower deployment cycles (AMI baking takes time)',
            'Higher operational overhead vs. Fargate or Lambda',
            'Instances cost money even when idle (unless using Spot + ASG scale-in)',
            'Security hardening (OS-level) is your responsibility']
    add_para(doc, '✅  Advantages:')
    for p in pros: add_bullet(doc, p)
    add_para(doc, '❌  Disadvantages:')
    for c in cons: add_bullet(doc, c)

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 3: LAMBDA
    # ─────────────────────────────────────────────────────────────────────────
    add_heading(doc, '3. AWS Lambda Deployment', level=1, color=AWS_ORANGE)

    add_heading(doc, '3.1  What is AWS Lambda?', level=2, color=SECTION_BLUE)
    add_para(doc,
        'AWS Lambda is a serverless compute service that runs your code in response to events '
        'without provisioning or managing servers. You upload your code (or container image), '
        'define triggers, and AWS handles execution, scaling, and fault tolerance automatically. '
        'Lambda scales from 0 to thousands of concurrent executions in milliseconds.')

    add_heading(doc, '3.2  Key Concepts', level=2, color=SECTION_BLUE)
    concepts = [
        ('Function', 'The unit of deployment — your code packaged as a ZIP or Docker image (up to 10 GB).'),
        ('Event Source / Trigger', 'What invokes your function: API Gateway, S3 events, SQS messages, '
                                    'EventBridge schedules, Kinesis streams, DynamoDB streams, etc.'),
        ('Execution Environment', 'An isolated micro-VM (Firecracker) provisioned by AWS. '
                                   'Stays warm for a few minutes between invocations.'),
        ('Concurrency', 'Default: 1000 concurrent executions per account. Can be increased. '
                        'Provisioned Concurrency keeps N environments warm to eliminate cold starts.'),
        ('Cold Start', 'First invocation after inactivity incurs ~100ms–2s latency for initialization. '
                       'Mitigated with Provisioned Concurrency or keeping containers warm.'),
        ('Pricing', 'Pay per 100ms of execution + number of invocations. First 1M requests/month free.'),
    ]
    for term, defn in concepts:
        p = doc.add_paragraph()
        p.add_run(term + ': ').bold = True
        p.add_run(defn)
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(3)

    add_heading(doc, '3.3  Architecture', level=2, color=SECTION_BLUE)
    if HAS_MPL:
        buf = make_lambda_diagram()
        add_image_buf(doc, buf, 6.2,
                      'Figure 2: AWS Lambda Deployment Architecture — Event-driven with multiple triggers and downstream integrations')
    add_separator(doc)

    add_heading(doc, '3.4  Deployment Steps', level=2, color=SECTION_BLUE)
    lambda_steps = [
        ('Step 1: Package Your Code',
         'Option A (ZIP): pip install -r requirements.txt -t ./package → zip -r function.zip . → '
         'aws lambda update-function-code\n'
         'Option B (Container): Build Docker image → push to ECR → Lambda uses container image. '
         'Recommended for ML models with heavy dependencies (PyTorch, TensorFlow).'),
        ('Step 2: Configure Lambda Function',
         'Set memory (128 MB – 10 GB), timeout (max 15 min), VPC settings (if accessing RDS), '
         'environment variables, and IAM execution role with least-privilege permissions.'),
        ('Step 3: Set Up API Gateway Trigger',
         'Create REST API or HTTP API in API Gateway. Define POST /predict route mapped to Lambda. '
         'Enable Lambda proxy integration. Configure throttling and CORS settings.'),
        ('Step 4: Handle Model Loading Efficiently',
         'Load model OUTSIDE the handler function (at module level) so it persists across warm invocations. '
         'Cache model weights in /tmp (512MB – 10GB) after downloading from S3 on first cold start.'),
        ('Step 5: Manage Concurrency',
         'Set reserved concurrency to limit function scale. Use Provisioned Concurrency for '
         'latency-sensitive ML endpoints to pre-warm containers and eliminate cold starts.'),
        ('Step 6: Deploy with SAM or CDK',
         'Use AWS SAM (Serverless Application Model) or AWS CDK for Infrastructure-as-Code deployment. '
         'sam deploy or cdk deploy provisions Lambda, API Gateway, and all IAM resources.'),
    ]
    for title_step, desc in lambda_steps:
        p = doc.add_paragraph()
        p.add_run(title_step).bold = True
        p.paragraph_format.space_before = Pt(6)
        add_para(doc, desc, indent=True)

    add_heading(doc, '3.5  Practical ML Scenario', level=2, color=SECTION_BLUE)
    add_para(doc,
        'Scenario: Real-time text classification using a lightweight DistilBERT model '
        '(50 MB) deployed as a Lambda container.\n')
    lambda_scenario = [
        'Container Image: Python 3.11 + transformers + PyTorch CPU + FastAPI (stored in ECR)',
        'Memory: 3008 MB (Lambda allocates CPU proportional to memory)',
        'Timeout: 30 seconds (inference < 500ms for short texts)',
        'Trigger: API Gateway HTTP API → Lambda (< 1ms routing overhead)',
        'Cold Start: ~2s on first invocation. Provisioned Concurrency = 5 keeps 5 warm',
        'Cost: 1M requests × 500ms × 3GB = ~$6.25/month vs EC2 at $50+/month for same load',
        'Scaling: Automatic — 100 users hit simultaneously → 100 Lambda instances spin up',
    ]
    for item in lambda_scenario:
        add_bullet(doc, item)

    add_para(doc, 'Lambda handler pattern for ML:')
    add_code_block(doc,
        '# Module-level: runs once per container lifecycle\n'
        'import torch, json\n'
        'model = load_model_from_s3()   # warm container reuses this\n\n'
        'def lambda_handler(event, context):\n'
        '    body = json.loads(event["body"])\n'
        '    prediction = model.predict(body["text"])\n'
        '    return {"statusCode": 200, "body": json.dumps(prediction)}')

    add_heading(doc, '3.6  Lambda Pros and Cons', level=2, color=SECTION_BLUE)
    pros = ['Zero infrastructure management — AWS handles everything',
            'True pay-per-use (no cost when idle)',
            'Automatic scaling to millions of concurrent requests',
            'Seamless event-driven integrations (S3, SQS, Kinesis, DynamoDB)',
            'Native support for canary deployments via Lambda aliases']
    cons = ['15-minute maximum execution time (not for long training jobs)',
            'Cold starts can add 100ms–3s latency (mitigated by Provisioned Concurrency)',
            '10 GB maximum memory — large models may not fit',
            'No persistent local disk (only /tmp ephemeral, 512MB–10GB)',
            'Debugging is harder (CloudWatch logs, X-Ray tracing required)']
    add_para(doc, '✅  Advantages:')
    for p in pros: add_bullet(doc, p)
    add_para(doc, '❌  Disadvantages:')
    for c in cons: add_bullet(doc, c)

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 4: ECS
    # ─────────────────────────────────────────────────────────────────────────
    add_heading(doc, '4. Amazon ECS — EC2 Launch Type vs AWS Fargate', level=1, color=AWS_ORANGE)

    add_heading(doc, '4.1  What is Amazon ECS?', level=2, color=SECTION_BLUE)
    add_para(doc,
        'Amazon Elastic Container Service (ECS) is a fully managed container orchestration service. '
        'It runs Docker containers in a cluster and handles scheduling, service discovery, '
        'load balancer integration, rolling deployments, and health monitoring.\n\n'
        'Unlike Kubernetes, ECS is an AWS-native, proprietary orchestrator that is simpler to '
        'operate but less portable. ECS supports two compute launch types: EC2 and Fargate.')

    add_heading(doc, '4.2  ECS EC2 Launch Type vs Fargate — The Core Difference', level=2, color=SECTION_BLUE)

    # Comparison table EC2 vs Fargate
    tbl = doc.add_table(rows=12, cols=3)
    tbl.style = 'Table Grid'
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ['Aspect', 'ECS — EC2 Launch Type', 'ECS — Fargate (Serverless)']
    colors_hdr = ['232F3E', 'FF9900', '22C55E']
    text_colors_hdr = [WHITE, AWS_DARK, WHITE]
    for ci, (h, bg, tc) in enumerate(zip(headers, colors_hdr, text_colors_hdr)):
        cell = tbl.rows[0].cells[ci]
        shade_cell(cell, bg)
        cell_text(cell, h, bold=True, color=tc, fontsize=9, align='center')

    rows_data = [
        ('Who manages EC2 workers?', 'YOU — patch, scale, monitor EC2', 'AWS — completely invisible to you'),
        ('Pricing model', 'Pay for EC2 instances (even if containers idle)', 'Pay per vCPU-second + GB-second used'),
        ('Infrastructure visibility', 'Full EC2 control (SSH, instance type, GPU)', 'No access to underlying instances'),
        ('GPU / custom instances', '✅ Yes — g4dn, p3, Inf1 supported', '❌ No GPU support in Fargate'),
        ('Startup time', 'EC2 boot: 2–5 min, Container: 10–30s', 'Task start: 20–60 seconds (micro-VM)'),
        ('Cost for always-on', 'More predictable, cheaper for high utilization', 'More expensive for 24/7 workloads'),
        ('Cost for bursty traffic', 'Need to over-provision or use ASG', 'Pay only when running — ideal for bursts'),
        ('Bin packing', 'ECS packs multiple containers per EC2', 'Each task gets dedicated compute'),
        ('Operational overhead', 'Medium — manage node lifecycle', 'Low — just define CPU/memory for task'),
        ('Networking', 'EC2 ENIs shared across tasks', 'Each task gets dedicated ENI (awsvpc)'),
        ('Best for', 'GPU workloads, long-running ML serving', 'Microservices, batch jobs, APIs'),
    ]
    row_bgs = ['FFFFFF', 'F9FAFB'] * 6
    for ri, (aspect, ec2val, fargateval) in enumerate(rows_data):
        bg = row_bgs[ri % 2]
        row = tbl.rows[ri + 1]
        shade_cell(row.cells[0], bg)
        shade_cell(row.cells[1], bg)
        shade_cell(row.cells[2], bg)
        cell_text(row.cells[0], aspect, bold=True, fontsize=8.5)
        cell_text(row.cells[1], ec2val, fontsize=8.5)
        cell_text(row.cells[2], fargateval, fontsize=8.5)

    doc.add_paragraph()

    add_heading(doc, '4.3  Architecture Diagrams', level=2, color=SECTION_BLUE)
    add_para(doc, 'The diagrams below show both ECS deployment modes side by side:')
    if HAS_MPL:
        buf = make_ecs_diagram()
        add_image_buf(doc, buf, 6.5,
                      'Figure 3: ECS — EC2 Launch Type (left) vs Fargate (right). '
                      'With EC2, you manage nodes. With Fargate, tasks float on AWS-managed infrastructure.')
    add_separator(doc)

    add_heading(doc, '4.4  Deployment Steps (ECS Fargate)', level=2, color=SECTION_BLUE)
    ecs_steps = [
        ('Step 1: Create ECR Repository and Push Image',
         'aws ecr create-repository --repository-name ml-api\n'
         'docker build -t ml-api:v1.0 .\n'
         'docker tag ml-api:v1.0 <account>.dkr.ecr.<region>.amazonaws.com/ml-api:v1.0\n'
         'docker push <account>.dkr.ecr.<region>.amazonaws.com/ml-api:v1.0'),
        ('Step 2: Define ECS Task Definition',
         'Specify: container image URI (ECR), CPU (e.g., 2048 = 2 vCPU), memory (4096 MB), '
         'port mappings (8000:8000), environment variables, IAM task role, and logging (CloudWatch).'),
        ('Step 3: Create ECS Cluster',
         'aws ecs create-cluster --cluster-name ml-cluster --capacity-providers FARGATE\n'
         'For EC2 launch type: also create EC2 Auto Scaling Group with ECS-optimized AMI.'),
        ('Step 4: Create ECS Service',
         'Define: desired count=3, launch type=FARGATE, VPC subnets, security groups, '
         'ALB target group integration, and deployment configuration (rolling update: min 50%, max 200%).'),
        ('Step 5: Fargate Auto Scaling',
         'Attach Application Auto Scaling to ECS service. Scale based on ALB request count per target '
         'or ECS service CPU utilization. Min=2, Max=20 tasks.'),
        ('Step 6: CI/CD with CodePipeline',
         'On git push: CodeBuild → docker build → push to ECR → CodePipeline triggers ECS deploy '
         '→ ECS performs rolling update (drains old tasks, starts new tasks with new image tag).'),
    ]
    for title_step, desc in ecs_steps:
        p = doc.add_paragraph()
        p.add_run(title_step).bold = True
        p.paragraph_format.space_before = Pt(6)
        add_code_block(doc, desc) if '\n' in desc and 'docker' in desc else add_para(doc, desc, indent=True)

    add_heading(doc, '4.5  Practical ML Scenario', level=2, color=SECTION_BLUE)
    add_para(doc,
        'Scenario: Containerized ML model API (FastAPI + PyTorch) with variable traffic '
        '— quiet nights, heavy daytime load.\n')
    ecs_scenario = [
        'Container: Docker image (Python + PyTorch CPU + FastAPI) pushed to ECR',
        'Fargate Task: 2 vCPU, 8 GB RAM — perfect for a 500MB BERT model serving',
        'Scaling: 2 tasks at night → 20 tasks during peak hours (based on ALB requests)',
        'Cost saving vs EC2: 60-80% reduction for variable traffic (no idle EC2 costs)',
        'Image update: Push new image to ECR → update service → ECS rolls out new tasks',
        'Secrets: Model API keys stored in AWS Secrets Manager, injected via task definition env vars',
        'GPU workload: Use ECS EC2 launch type with g4dn.xlarge instead (Fargate has no GPU)',
    ]
    for item in ecs_scenario:
        add_bullet(doc, item)

    add_heading(doc, '4.6  ECS Pros and Cons', level=2, color=SECTION_BLUE)
    pros = ['AWS-native — deep integration with ALB, IAM, CloudWatch, CodeDeploy',
            'Fargate: zero node management — focus on containers, not servers',
            'Strong auto-scaling support (task-level, not instance-level)',
            'Simpler than Kubernetes for teams not familiar with K8s',
            'Rolling and blue/green deployments built-in']
    cons = ['AWS-proprietary — less portable than Kubernetes',
            'Limited ecosystem (no Helm charts, CRDs, or service mesh in native form)',
            'Fargate has no GPU support — need EC2 launch type for ML GPU workloads',
            'Complex multi-service architectures can become hard to manage without K8s features',
            'ECS EC2 launch type still requires EC2 management']
    add_para(doc, '✅  Advantages:')
    for p in pros: add_bullet(doc, p)
    add_para(doc, '❌  Disadvantages:')
    for c in cons: add_bullet(doc, c)

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 5: EKS
    # ─────────────────────────────────────────────────────────────────────────
    add_heading(doc, '5. Amazon EKS — Kubernetes Deployment', level=1, color=AWS_ORANGE)

    add_heading(doc, '5.1  What is Amazon EKS?', level=2, color=SECTION_BLUE)
    add_para(doc,
        'Amazon Elastic Kubernetes Service (EKS) is a fully managed Kubernetes control plane. '
        'AWS runs and maintains the etcd database, API server, scheduler, and controller manager '
        'across three Availability Zones. You only manage the worker nodes (or use Fargate profiles '
        'or Karpenter for serverless nodes).\n\n'
        'EKS is the right choice when you need full Kubernetes features: Helm charts, Custom Resource '
        'Definitions (CRDs), Istio service mesh, RBAC, GitOps with Flux/ArgoCD, multi-tenant clusters, '
        'or when portability across cloud providers matters.')

    add_heading(doc, '5.2  EKS Architecture', level=2, color=SECTION_BLUE)
    if HAS_MPL:
        buf = make_eks_diagram()
        add_image_buf(doc, buf, 6.5,
                      'Figure 4: Amazon EKS Architecture — Managed control plane + worker node groups + '
                      'Fargate profiles with Ingress, IRSA, and ECR integration.')
    add_separator(doc)

    add_heading(doc, '5.3  Key EKS Components', level=2, color=SECTION_BLUE)
    eks_concepts = [
        ('Managed Control Plane', 'API Server, etcd, Scheduler, Controller Manager — all run by AWS, HA across 3 AZs. Cost: $0.10/hr per cluster.'),
        ('Node Groups', 'EC2 instances that run Pods. Managed Node Groups: AWS automates AMI updates and node draining. Self-managed: full control.'),
        ('Fargate Profiles', 'Serverless nodes — define namespace/label selectors, pods matching those rules run on Fargate (no EC2 management).'),
        ('Karpenter', 'Open-source autoscaler (better than Cluster Autoscaler). Provisions right-sized EC2 instances within seconds when pod pending.'),
        ('AWS Load Balancer Controller', 'Creates ALB (Application) or NLB (Network) load balancers from Kubernetes Ingress/Service objects.'),
        ('IRSA (IAM Roles for Service Accounts)', 'Pods get fine-grained AWS IAM permissions without node-level credentials. Security best practice.'),
        ('Amazon ECR', 'Private container registry integrated with EKS — no credential management for image pulls.'),
        ('CoreDNS / kube-proxy', 'Cluster DNS and network proxy — AWS maintains these add-ons on EKS clusters.'),
    ]
    for term, defn in eks_concepts:
        p = doc.add_paragraph()
        p.add_run(term + ': ').bold = True
        p.add_run(defn)
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(4)

    add_heading(doc, '5.4  Deployment Steps', level=2, color=SECTION_BLUE)
    eks_steps = [
        ('Step 1: Create EKS Cluster',
         'eksctl create cluster --name ml-cluster --region us-east-1 \\\n'
         '  --nodegroup-name ml-nodes --node-type m5.xlarge \\\n'
         '  --nodes 3 --nodes-min 2 --nodes-max 10 --managed'),
        ('Step 2: Push Image to ECR',
         'docker build -t ml-api:v1.0 .\n'
         'docker push <account>.dkr.ecr.<region>.amazonaws.com/ml-api:v1.0'),
        ('Step 3: Write Kubernetes Manifests',
         'Create: Deployment (replicas, image, resources), Service (ClusterIP), '
         'Ingress (ALB), HorizontalPodAutoscaler (HPA), and ConfigMap/Secret objects.'),
        ('Step 4: Deploy to EKS',
         'kubectl apply -f deployment.yaml\n'
         'kubectl apply -f service.yaml\n'
         'kubectl apply -f ingress.yaml   # Creates ALB via AWS LB Controller\n'
         '# Or use Helm:\n'
         'helm upgrade --install ml-api ./helm/ml-api -n ml-prod'),
        ('Step 5: Set Up GitOps (Optional but recommended)',
         'Install ArgoCD or Flux. On git push to main branch → ArgoCD syncs cluster state '
         'with git repository. Zero-touch deployment with rollback via git revert.'),
        ('Step 6: Configure Karpenter Autoscaling',
         'Karpenter watches for pending pods → provisions matching EC2 instance type within 60s. '
         'Consolidates underutilized nodes automatically. Define NodePool with instance family constraints.'),
    ]
    for title_step, desc in eks_steps:
        p = doc.add_paragraph()
        p.add_run(title_step).bold = True
        p.paragraph_format.space_before = Pt(6)
        add_code_block(doc, desc) if '\n' in desc else add_para(doc, desc, indent=True)

    add_heading(doc, '5.5  Sample Kubernetes Deployment Manifest', level=2, color=SECTION_BLUE)
    add_code_block(doc,
        'apiVersion: apps/v1\n'
        'kind: Deployment\n'
        'metadata:\n'
        '  name: ml-api\n'
        '  namespace: ml-prod\n'
        'spec:\n'
        '  replicas: 3\n'
        '  selector:\n'
        '    matchLabels:\n'
        '      app: ml-api\n'
        '  template:\n'
        '    metadata:\n'
        '      labels:\n'
        '        app: ml-api\n'
        '    spec:\n'
        '      serviceAccountName: ml-api-sa   # IRSA — grants S3 access\n'
        '      containers:\n'
        '      - name: ml-api\n'
        '        image: <account>.dkr.ecr.us-east-1.amazonaws.com/ml-api:v1.0\n'
        '        ports:\n'
        '        - containerPort: 8000\n'
        '        resources:\n'
        '          requests:\n'
        '            cpu: "1"\n'
        '            memory: "4Gi"\n'
        '          limits:\n'
        '            cpu: "2"\n'
        '            memory: "8Gi"\n'
        '        env:\n'
        '        - name: MODEL_PATH\n'
        '          value: "s3://my-models/bert-v2.pt"\n'
        '---\n'
        'apiVersion: autoscaling/v2\n'
        'kind: HorizontalPodAutoscaler\n'
        'metadata:\n'
        '  name: ml-api-hpa\n'
        'spec:\n'
        '  scaleTargetRef:\n'
        '    apiVersion: apps/v1\n'
        '    kind: Deployment\n'
        '    name: ml-api\n'
        '  minReplicas: 2\n'
        '  maxReplicas: 50\n'
        '  metrics:\n'
        '  - type: Resource\n'
        '    resource:\n'
        '      name: cpu\n'
        '      target:\n'
        '        type: Utilization\n'
        '        averageUtilization: 60')

    add_heading(doc, '5.6  Practical ML Scenario', level=2, color=SECTION_BLUE)
    add_para(doc,
        'Scenario: Multi-model ML platform serving 10 different models '
        '(NLP, CV, Tabular) with A/B testing, canary deployments, and GPU scheduling.\n')
    eks_scenario = [
        'Cluster: EKS with 2 node groups — m5.2xlarge (general) + g4dn.xlarge (GPU)',
        'GPU pods: Use nvidia.com/gpu: 1 resource request → Karpenter provisions g4dn nodes',
        'Multiple models: Each model = separate Deployment + Service in own namespace',
        'A/B Testing: Use Istio VirtualService to route 90% traffic to v1, 10% to v2',
        'Canary deploy: ArgoCD Rollouts — automated canary with Prometheus metrics gate',
        'IRSA: ml-api ServiceAccount mapped to IAM role → S3:GetObject on model bucket only',
        'Cost: $0.10/hr (control plane) + EC2 nodes (Karpenter scale-to-zero when idle)',
        'Portability: Same Helm charts work on EKS, GKE, AKS — full cloud-agnostic capability',
    ]
    for item in eks_scenario:
        add_bullet(doc, item)

    add_heading(doc, '5.7  EKS Pros and Cons', level=2, color=SECTION_BLUE)
    pros = ['Industry-standard Kubernetes — full feature set (CRDs, RBAC, Helm, service mesh)',
            'Cloud-agnostic workloads — same manifests work on any K8s cluster',
            'Advanced deployment strategies: canary, blue/green, A/B via Argo Rollouts',
            'GPU scheduling with node affinity and taints/tolerations',
            'Karpenter: fastest node autoscaling (60s from pending pod to running)']
    cons = ['Steep learning curve — Kubernetes expertise required',
            '$0.10/hr cluster control plane cost (even with no workloads)',
            'Higher operational overhead: version upgrades, add-on management',
            'More complex debugging vs ECS or Lambda',
            'Over-engineering for simple applications — don\'t use K8s if ECS/Fargate suffices']
    add_para(doc, '✅  Advantages:')
    for p in pros: add_bullet(doc, p)
    add_para(doc, '❌  Disadvantages:')
    for c in cons: add_bullet(doc, c)

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 6: COMPARISON TABLE
    # ─────────────────────────────────────────────────────────────────────────
    add_heading(doc, '6. Side-by-Side Comparison', level=1, color=AWS_ORANGE)

    if HAS_MPL:
        buf = make_comparison_diagram()
        add_image_buf(doc, buf, 6.3,
                      'Figure 5: Comparison matrix across key dimensions — filled circles indicate relative strength.')
    add_separator(doc)

    # Full comparison table
    add_heading(doc, '6.1  Detailed Comparison Table', level=2, color=SECTION_BLUE)

    criteria_list = [
        'Abstraction Level', 'Infrastructure Mgmt', 'Pricing Model', 'GPU Support',
        'Max Execution Time', 'Cold Start', 'Portability', 'Deployment Speed',
        'Autoscaling Unit', 'Max Scale', 'Kubernetes Features', 'CI/CD Integration',
        'Observability', 'Networking', 'Security Boundary', 'Best Use Case',
    ]
    data_table = {
        'EC2':         ['Low (VM)', 'High (you manage all)', 'Per hour (+ EBS)',
                        '✅ Full GPU support', 'Unlimited', 'None (always on)', 'Low (AMI specific)',
                        'Slow (AMI bake + ASG)', 'EC2 Instance', 'Hundreds of instances',
                        '❌ None', 'CodeDeploy / GitHub Actions', 'CloudWatch + SSM',
                        'ENI per instance', 'OS-level isolation', 'Stateful apps, GPU ML, legacy'],
        'Lambda':      ['Highest (function)', 'None (zero ops)', 'Per invocation + ms',
                        '❌ No GPU', '15 minutes', 'Yes (100ms-3s)', 'Medium (ZIP/container)',
                        'Instant (code deploy)', 'Function instance', '1000+ concurrent',
                        '❌ None', 'SAM / CDK / Serverless Framework', 'X-Ray + CloudWatch',
                        'ENI per function (VPC)', 'Micro-VM isolation', 'Event-driven, lightweight inference'],
        'ECS (EC2)':   ['Medium (container)', 'Medium (manage EC2)', 'Per EC2 instance',
                        '✅ GPU via EC2', 'Unlimited', 'Container: 10-30s', 'Medium (Docker)',
                        'Fast (rolling update)', 'ECS Task', 'Hundreds of tasks',
                        '❌ Limited', 'CodePipeline / GitHub Actions', 'Container Insights + CW',
                        'EC2 ENI shared', 'Container isolation', 'Containerized services, GPU ML'],
        'ECS (Fargate)':['Medium-High', 'Low (serverless nodes)', 'Per vCPU-sec + GB-sec',
                         '❌ No GPU', 'Unlimited', 'Task: 20-60s', 'Medium (Docker)',
                         'Fast (rolling update)', 'ECS Task', 'Hundreds of tasks',
                         '❌ Limited', 'CodePipeline / GitHub Actions', 'Container Insights + CW',
                         'ENI per task (awsvpc)', 'Task-level isolation', 'Serverless containers, APIs'],
        'EKS':         ['Medium (K8s objects)', 'Medium-High (node mgmt)', 'EC2 + $0.10/hr cluster',
                        '✅ GPU with node taints', 'Unlimited', 'Pod: 5-30s', 'High (K8s standard)',
                        'Fast (kubectl/Helm)', 'Pod / Node', 'Thousands of pods',
                        '✅ Full K8s features', 'ArgoCD / Flux / GitHub Actions', 'CloudWatch + Prometheus',
                        'Pod-level ENI (VPC CNI)', 'Namespace/RBAC', 'Complex ML platforms, multi-team'],
    }

    headers2 = ['Criteria', 'EC2', 'Lambda', 'ECS (EC2)', 'ECS (Fargate)', 'EKS']
    tbl2 = doc.add_table(rows=len(criteria_list)+1, cols=6)
    tbl2.style = 'Table Grid'
    tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr_colors2 = ['232F3E','FF9900','FF9900','17A2B8','22C55E','8B5CF6']
    hdr_txt_clrs = [WHITE,     AWS_DARK,AWS_DARK,WHITE,    WHITE,   WHITE]
    for ci, (h, bg, tc) in enumerate(zip(headers2, hdr_colors2, hdr_txt_clrs)):
        cell = tbl2.rows[0].cells[ci]
        shade_cell(cell, bg)
        cell_text(cell, h, bold=True, color=tc, fontsize=8, align='center')

    providers_order = ['EC2','Lambda','ECS (EC2)','ECS (Fargate)','EKS']
    for ri, crit in enumerate(criteria_list):
        bg = 'FFFFFF' if ri%2==0 else 'F9FAFB'
        row = tbl2.rows[ri+1]
        shade_cell(row.cells[0], bg)
        cell_text(row.cells[0], crit, bold=True, fontsize=8)
        for ci, prov in enumerate(providers_order):
            shade_cell(row.cells[ci+1], bg)
            val = data_table[prov][ri]
            cell_text(row.cells[ci+1], val, fontsize=7.5)

    doc.add_paragraph()
    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 7: DECISION GUIDE
    # ─────────────────────────────────────────────────────────────────────────
    add_heading(doc, '7. Decision Guide — When to Choose Which Option', level=1, color=AWS_ORANGE)

    if HAS_MPL:
        buf = make_decision_diagram()
        add_image_buf(doc, buf, 6.0,
                      'Figure 6: Decision flowchart to select the right AWS deployment option.')
    add_separator(doc)

    add_heading(doc, '7.1  Choose EC2 When:', level=2, color=SECTION_BLUE)
    ec2_when = [
        'You need GPU instances (g4dn, p3, p4, Inf1, Trn1) for deep learning training or GPU inference',
        'You have existing on-premise applications to lift-and-shift without containerizing',
        'Your application requires persistent disk I/O, specific kernel versions, or OS-level customization',
        'You need very long-running processes (days/weeks) like large model training jobs',
        'Your team is more familiar with Linux administration than containers/Kubernetes',
        'Cost predictability is critical — reserved instances offer up to 72% savings vs on-demand',
    ]
    for item in ec2_when: add_bullet(doc, item)

    add_heading(doc, '7.2  Choose Lambda When:', level=2, color=SECTION_BLUE)
    lambda_when = [
        'Your function executes in < 15 minutes and is triggered by events (S3, API calls, messages)',
        'Traffic is unpredictable or highly variable — Lambda scales to zero, paying nothing when idle',
        'You\'re building event-driven architectures (ETL pipelines, webhook processors, async tasks)',
        'The ML model is lightweight (< 3 GB) and inference time is under a few seconds',
        'You want the absolute minimum operational overhead — no servers, no patches, no containers',
        'Cost is the primary concern for low-volume applications (< 1M requests/month can be nearly free)',
    ]
    for item in lambda_when: add_bullet(doc, item)

    add_heading(doc, '7.3  Choose ECS Fargate When:', level=2, color=SECTION_BLUE)
    fargate_when = [
        'Your application is containerized (Docker) but you don\'t want to manage EC2 nodes',
        'Traffic is variable with periods of low usage — Fargate scales to exactly what you need',
        'You need longer execution times than Lambda allows (> 15 minutes) but want serverless convenience',
        'You\'re running microservices that communicate via APIs and need reliable container isolation',
        'The team knows Docker but not Kubernetes, and you want simple AWS-native orchestration',
        'GPU is NOT required — use ECS EC2 launch type instead if GPU is needed',
    ]
    for item in fargate_when: add_bullet(doc, item)

    add_heading(doc, '7.4  Choose EKS When:', level=2, color=SECTION_BLUE)
    eks_when = [
        'You\'re running a complex multi-service ML platform with 10+ microservices',
        'You need advanced deployment patterns: canary releases, A/B testing, feature flags',
        'Your team uses Helm charts, ArgoCD, Istio, or other Kubernetes-native tooling',
        'Multi-cloud portability is required — same workloads must run on GKE or AKS too',
        'You need fine-grained resource management: CPU/memory requests, QoS classes, taints/tolerations',
        'You\'re already running Kubernetes on-premise and extending to AWS',
    ]
    for item in eks_when: add_bullet(doc, item)

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 8: COST
    # ─────────────────────────────────────────────────────────────────────────
    add_heading(doc, '8. Cost Comparison — Practical Example', level=1, color=AWS_ORANGE)
    add_para(doc,
        'Scenario: ML inference API serving 1 million requests/month, each taking 500ms, '
        'requiring 2 vCPU and 4 GB RAM. Region: us-east-1.')
    doc.add_paragraph()

    cost_data = [
        ('EC2 (3× m5.large, On-Demand)', '$0.096/hr × 3 × 720hrs', '$207/month',
         'Fixed cost regardless of actual traffic. Savings with Reserved: ~$120/mo'),
        ('EC2 (Spot Instances)', '$0.029/hr × 3 × 720hrs + On-demand for base', '$63/month',
         'Up to 70% savings. Risk of interruption — use with checkpointing'),
        ('Lambda (container)', '1M × $0.0000002 + 1M × 500ms × 2GB × $0.0000166667', '$20/month',
         'Cost scales to zero. Cheapest for variable/low traffic. Cold starts apply.'),
        ('ECS Fargate', '3 tasks × 2vCPU × $0.04048/vCPU-hr + 4GB × $0.004445/GB-hr', '$230/month',
         'Scale to 0 in off-hours → ~$80/mo with autoscaling. No idle cost.'),
        ('EKS (m5.large nodes)', '$0.10/hr (control plane) + $0.096/hr × 3 nodes × 720hrs', '$277/month',
         'Includes cluster fee. Karpenter + Spot nodes → ~$90/mo with optimization.'),
    ]

    tbl3 = doc.add_table(rows=len(cost_data)+1, cols=4)
    tbl3.style = 'Table Grid'
    tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
    cost_headers = ['Deployment Option', 'Cost Calculation', 'Est. Monthly Cost', 'Notes']
    for ci, h in enumerate(cost_headers):
        cell = tbl3.rows[0].cells[ci]
        shade_cell(cell, '232F3E')
        cell_text(cell, h, bold=True, color=WHITE, fontsize=9, align='center')

    for ri, (opt, calc, cost, note) in enumerate(cost_data):
        bg = 'FFFFFF' if ri%2==0 else 'F9FAFB'
        row = tbl3.rows[ri+1]
        for ci in range(4): shade_cell(row.cells[ci], bg)
        cell_text(row.cells[0], opt, bold=True, fontsize=8.5)
        cell_text(row.cells[1], calc, fontsize=8)
        cell_text(row.cells[2], cost, bold=True, fontsize=9, color=GREEN)
        cell_text(row.cells[3], note, fontsize=7.5)

    doc.add_paragraph()
    p_note = doc.add_paragraph()
    r = p_note.add_run(
        '* Costs are approximate (us-east-1, 2024 pricing). '
        'Actual costs vary based on data transfer, storage, and usage patterns. '
        'Use AWS Pricing Calculator for exact estimates.')
    r.font.italic = True
    r.font.size = Pt(8.5)
    r.font.color.rgb = GRAY

    doc.add_page_break()

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 9: SUMMARY
    # ─────────────────────────────────────────────────────────────────────────
    add_heading(doc, '9. Summary & Recommendations', level=1, color=AWS_ORANGE)

    add_heading(doc, '9.1  Quick Reference Summary', level=2, color=SECTION_BLUE)
    summary_items = [
        ('🖥 EC2', 'Maximum control, GPU support. Highest ops overhead. '
                   'Ideal for: GPU inference, stateful apps, large model training.'),
        ('⚡ Lambda', 'Zero-ops serverless. Event-driven. Max 15 min. '
                      'Ideal for: Lightweight ML inference, ETL, async processing, low-traffic APIs.'),
        ('📦 ECS/Fargate', 'Serverless containers. No node management. AWS-native. '
                            'Ideal for: Containerized APIs, microservices, variable traffic.'),
        ('📦 ECS/EC2', 'Containers on your EC2. GPU support. '
                        'Ideal for: GPU containers, predictable high-throughput workloads.'),
        ('☸ EKS', 'Full Kubernetes. Cloud-agnostic. Most powerful. Most complex. '
                   'Ideal for: Multi-model platforms, teams with K8s expertise, advanced orchestration.'),
    ]
    for icon_title, desc in summary_items:
        p = doc.add_paragraph()
        p.add_run(icon_title + ':  ').bold = True
        p.add_run(desc)
        p.paragraph_format.space_after = Pt(5)

    add_heading(doc, '9.2  Recommended Path for ML Teams', level=2, color=SECTION_BLUE)
    path_items = [
        ('Stage 1 — Prototype / POC',
         'Start with Lambda + API Gateway. Fastest to deploy. Test if your model fits within '
         'Lambda constraints (size, latency, execution time).'),
        ('Stage 2 — Production API (Low-Medium Scale)',
         'Migrate to ECS Fargate. Containerize with Docker. Add ALB and auto-scaling. '
         'Still zero node management but more control than Lambda.'),
        ('Stage 3 — GPU or High-Performance Requirements',
         'Switch to ECS EC2 launch type with GPU instances, or EC2 with Auto Scaling Groups '
         'if you need maximum throughput or specialized hardware.'),
        ('Stage 4 — Platform Scale / Multi-Model',
         'Graduate to EKS when: (a) managing 5+ services, (b) need K8s-native tooling, '
         '(c) running A/B tests or canary deployments, (d) require multi-cloud portability.'),
    ]
    for stage, desc in path_items:
        p = doc.add_paragraph()
        p.add_run(stage + ': ').bold = True
        p.add_run(desc)
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(6)

    add_heading(doc, '9.3  Golden Rules', level=2, color=SECTION_BLUE)
    golden_rules = [
        'Do NOT use EKS for a single-service application — Fargate is sufficient and simpler.',
        'Always use Spot Instances or Savings Plans for EC2 to reduce costs by 50-70%.',
        'Lambda is not free for high-throughput workloads — calculate break-even vs Fargate.',
        'Always store model weights in S3 — never bake large files into Docker images.',
        'Use IRSA for EKS / Task Roles for ECS — never hardcode AWS credentials in code.',
        'Enable CloudWatch Container Insights / X-Ray from day 1 — you cannot debug what you cannot see.',
        'Tag all resources (environment, team, project) — required for cost attribution at scale.',
    ]
    for rule in golden_rules:
        add_bullet(doc, '📌  ' + rule)

    doc.add_paragraph()
    closing = doc.add_paragraph()
    closing.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = closing.add_run(
        '─── End of Document ───\n\n'
        'For questions, reach out to your AWS Solutions Architect or refer to:\n'
        'https://aws.amazon.com/architecture/ | https://docs.aws.amazon.com')
    cr.font.color.rgb = GRAY
    cr.font.size = Pt(9)
    cr.font.italic = True

    # ─────────────────────────────────────────────────────────────────────────
    # SAVE
    # ─────────────────────────────────────────────────────────────────────────
    out_path = '/Users/sachinmishra/Desktop/GenAI/AWS_Deployment_Options_Guide.docx'
    doc.save(out_path)
    print(f'✅ Document saved: {out_path}')
    return out_path

if __name__ == '__main__':
    print('Building document...')
    if not HAS_MPL:
        print('WARNING: matplotlib not found — diagrams will be skipped')
    path = build_document()
    print(f'Done! → {path}')
