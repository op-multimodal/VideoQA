import torch
import torch.nn as nn
from attention import Attention
from language_model import WordEmbedding,QuestionEmbedding
import torch.nn.functional as F
from video_model import VideoEmbedding,Videofc
from fc import FCNet
from answer_model import AnswerEmbedding
from rela_model import Rela_Module
import config
import numpy as np



class BaseModel(nn.Module):
    def __init__(self,w_emb,q_emb,v_emb,a_emb,v_att,v_fc,r_emb,r_att,opt):
        super(BaseModel,self).__init__()
        #opt=config.parse_opt()
        self.opt=opt
        self.w_emb=w_emb
        self.q_emb=q_emb
        self.v_emb=v_emb
        self.a_emb=a_emb
        self.v_att=v_att
        self.r_att = r_att
        self.score=nn.Linear(self.opt.NUM_HIDDEN,1)
        self.v_fc = v_fc
        self.r_emb = r_emb
        self.softmax=nn.Softmax()

    def forward(self,v,q,a1,a2,a3,a4,a5):
        self.opt=config.parse_opt()
        w_emb=self.w_emb(q)
        emb1=self.w_emb(a1)
        emb2=self.w_emb(a2)
        emb3=self.w_emb(a3)
        emb4=self.w_emb(a4)
        emb5=self.w_emb(a5)
        print(v.shape)
        q_emb=self.q_emb(w_emb)
        #print(q_emb.shape)
        v_emb = self.v_fc(v)
        
        #print(v_emb.shape)
        r_emb = self.r_emb(v_emb,q_emb)
        #print(r_emb.shape)
        w_att = self.v_att(v_emb,q_emb)
        v_att = v_emb * w_att
        vatt = torch.squeeze(torch.sum(v_att,1,keepdim=True))
        
        wr_att = self.r_att(r_emb,q_emb)
        r_att = r_emb * wr_att
        ratt = torch.squeeze(torch.sum(r_att,1,keepdim=True))
        #print(ratt.shape)
         
        joint_proj = vatt + q_emb
        #print(joint_proj.shape)
        joint_proj = joint_proj + ratt
        
        cand1=self.score(self.a_emb(emb1,joint_proj))
        cand2=self.score(self.a_emb(emb2,joint_proj))
        cand3=self.score(self.a_emb(emb3,joint_proj))
        cand4=self.score(self.a_emb(emb4,joint_proj))
        cand5=self.score(self.a_emb(emb5,joint_proj))
        
        score=torch.from_numpy(np.zeros((v.size(0),5),dtype=np.float32))
        score[:,0]=torch.squeeze(cand1)
        score[:,1]=torch.squeeze(cand2)
        score[:,2]=torch.squeeze(cand3)
        score[:,3]=torch.squeeze(cand4)
        score[:,4]=torch.squeeze(cand5)
        return score

def build_baseline(dataset,opt):
    opt=config.parse_opt()
    w_emb=WordEmbedding(dataset.dictionary.ntokens(),300,opt.EMB_DROPOUT)
    q_emb=QuestionEmbedding(300,opt.NUM_HIDDEN,opt.NUM_LAYER,opt.BIDIRECT,opt.L_RNN_DROPOUT)
    v_emb=VideoEmbedding(opt.C3D_SIZE+opt.RES_SIZE,opt.NUM_HIDDEN,opt.NUM_LAYER,opt.BIDIRECT,opt.L_RNN_DROPOUT)
    v_att=Attention(opt.NUM_HIDDEN,opt.MID_DIM,opt.FC_DROPOUT)
    r_att=Attention(opt.NUM_HIDDEN,opt.MID_DIM,opt.FC_DROPOUT)
    v_fc=Videofc(opt.GLIMPSE,opt.C3D_SIZE+opt.RES_SIZE,opt.NUM_HIDDEN,opt.FC_DROPOUT)
    a_emb=AnswerEmbedding(300,opt.NUM_HIDDEN,opt.NUM_LAYER,opt.BIDIRECT,opt.L_RNN_DROPOUT)
    rela_emb = Rela_Module(opt.NUM_HIDDEN*3,opt.NUM_HIDDEN,opt.NUM_HIDDEN,opt.FC_DROPOUT)
    return BaseModel(w_emb,q_emb,v_emb,a_emb,v_att,v_fc,rela_emb,r_att,opt)

