import pygame, random, math, json
from pathlib import Path

pygame.init()
W,H,FPS=1200,760,60
CELL,COLS,ROWS=24,46,26
BX,BY=(W-COLS*CELL)//2,105
WHITE=(235,242,250); MUTED=(145,160,178); GREEN=(67,220,125)
CYAN=(61,207,255); GOLD=(255,201,76); PURPLE=(174,105,255)
RED=(245,76,82); PANEL=(16,23,35); GRID=(25,35,49)
SAVE=Path("snake_save.json")

def text(s,t,f,c,p,anchor="topleft"):
    r=f.render(t,True,c); setattr(r.get_rect(),anchor,p); rr=r.get_rect(); setattr(rr,anchor,p); s.blit(f.render(t,True,c),rr)

def center(p): return BX+p[0]*CELL+CELL//2, BY+p[1]*CELL+CELL//2
def free(used):
    for _ in range(3000):
        p=(random.randrange(COLS),random.randrange(ROWS))
        if p not in used:return p
    return (2,2)

class Particle:
    def __init__(self,p,c):
        self.x,self.y=p;a=random.random()*6.283;s=random.uniform(50,190)
        self.vx,self.vy=math.cos(a)*s,math.sin(a)*s
        self.life=self.max=random.uniform(.4,1);self.c=c;self.sz=random.uniform(2,5)
    def update(self,dt):
        self.x+=self.vx*dt;self.y+=self.vy*dt;self.vx*=.96;self.vy*=.96;self.life-=dt
    def draw(self,s):
        if self.life<=0:return
        a=int(255*self.life/self.max); q=max(1,int(self.sz))
        z=pygame.Surface((q*2+4,q*2+4),pygame.SRCALPHA)
        pygame.draw.circle(z,(*self.c,a),(q+2,q+2),q);s.blit(z,(self.x-q-2,self.y-q-2))

class Game:
    def __init__(self):
        self.fs=pygame.font.SysFont("segoeui",17);self.f=pygame.font.SysFont("segoeui",22)
        self.big=pygame.font.SysFont("segoeui",42,True);self.huge=pygame.font.SysFont("segoeui",64,True)
        self.mono=pygame.font.SysFont("consolas",18);self.best=0
        try:self.best=json.loads(SAVE.read_text())["best"]
        except:pass
        self.state="menu";self.mode="classic";self.reset()
    def reset(self):
        c=(COLS//2,ROWS//2)
        self.snake=[c,(c[0]-1,c[1]),(c[0]-2,c[1])]
        self.d=(1,0);self.nd=(1,0);self.turn=False
        self.score=0;self.level=1;self.speed=7.5;self.acc=0;self.elapsed=0
        self.combo=0;self.combo_t=0;self.flash=0;self.shake=0;self.paused=False
        self.parts=[];self.shield=False;self.boost=0;self.msg="";self.msg_t=0
        self.obstacles=set();self.food=None;self.kind="normal";self.power=None
        self.make_obstacles();self.spawn_food()
    def save(self):
        try:SAVE.write_text(json.dumps({"best":self.best}))
        except:pass
    def make_obstacles(self):
        n=(5+self.level//2 if self.mode=="classic" else 12+self.level if self.mode=="hard" else 20+self.level*2)
        for _ in range(n):
            p=free(set(self.snake)|self.obstacles|({self.food} if self.food else set()))
            if abs(p[0]-COLS//2)+abs(p[1]-ROWS//2)>6:self.obstacles.add(p)
    def spawn_food(self):
        self.food=free(set(self.snake)|self.obstacles)
        r=random.random();self.kind="normal" if r<.78 else "gold" if r<.92 else "speed"
    def start(self):self.reset();self.state="playing"
    def direction(self,d):
        if not self.turn and d!=(-self.d[0],-self.d[1]) and d!=self.d:self.nd=d;self.turn=True
    def eat(self):
        val={"normal":10,"gold":30,"speed":20}[self.kind];col={"normal":GREEN,"gold":GOLD,"speed":CYAN}[self.kind]
        self.combo+=1;self.combo_t=3;gain=int(val*min(4,1+(self.combo-1)*.15));self.score+=gain
        x,y=center(self.food)
        self.parts += [Particle((x,y),col) for _ in range(24)]
        self.shake=3;self.flash=.1
        if self.kind=="speed":self.boost=5;self.msg="SPEED BOOST"
        elif self.kind=="gold":self.msg=f"+{gain} GOLD"
        self.msg_t=1
        old=self.level;self.level=1+self.score//100;self.speed=min(18,7.5+(self.level-1)*.65)
        if self.level>old:self.msg=f"LEVEL {self.level}";self.msg_t=1.4;self.make_obstacles()
        if self.score>self.best:self.best=self.score;self.save()
        self.spawn_food()
        if not self.power and random.random()<.13:self.power=free(set(self.snake)|self.obstacles|{self.food})
    def die(self,reason):
        if self.shield:self.shield=False;self.msg="SHIELD SAVED YOU";self.msg_t=1.3;self.shake=7;return
        self.state="over";self.reason=reason;self.save()
    def move(self):
        self.d=self.nd;self.turn=False;hx,hy=self.snake[0];dx,dy=self.d;n=(hx+dx,hy+dy)
        if self.mode=="classic":n=(n[0]%COLS,n[1]%ROWS)
        elif not(0<=n[0]<COLS and 0<=n[1]<ROWS):return self.die("WALL COLLISION")
        if n in set(self.snake[:-1]):return self.die("SELF COLLISION")
        if n in self.obstacles:return self.die("OBSTACLE HIT")
        self.snake.insert(0,n)
        if n==self.food:self.eat()
        else:self.snake.pop()
        if self.power and n==self.power:
            self.power=None;self.shield=True;self.msg="SHIELD ONLINE";self.msg_t=1.2
    def update(self,dt):
        self.elapsed+=dt;self.flash=max(0,self.flash-dt);self.shake=max(0,self.shake-dt*20)
        self.msg_t=max(0,self.msg_t-dt);self.combo_t=max(0,self.combo_t-dt)
        if self.combo_t<=0:self.combo=0
        for p in self.parts[:]:
            p.update(dt)
            if p.life<=0:self.parts.remove(p)
        if self.state!="playing" or self.paused:return
        self.boost=max(0,self.boost-dt);self.acc+=dt
        step=1/(self.speed*(.68 if self.boost else 1))
        while self.acc>=step:self.acc-=step;self.move()
    def board(self,s):
        r=pygame.Rect(BX,BY,COLS*CELL,ROWS*CELL);pygame.draw.rect(s,PANEL,r,border_radius=14)
        for x in range(COLS+1):pygame.draw.line(s,GRID,(BX+x*CELL,BY),(BX+x*CELL,BY+ROWS*CELL))
        for y in range(ROWS+1):pygame.draw.line(s,GRID,(BX,BY+y*CELL),(BX+COLS*CELL,BY+y*CELL))
        for x,y in self.obstacles:
            rr=pygame.Rect(BX+x*CELL+3,BY+y*CELL+3,CELL-6,CELL-6);pygame.draw.rect(s,(70,78,90),rr,border_radius=5)
        if self.power:
            x,y=center(self.power);pygame.draw.circle(s,PURPLE,(x,y),8,2);pygame.draw.circle(s,PURPLE,(x,y),4)
        x,y=center(self.food);fc={"normal":GREEN,"gold":GOLD,"speed":CYAN}[self.kind]
        q=1+math.sin(self.elapsed*5)*.1;pygame.draw.circle(s,tuple(v//2 for v in fc),(x,y),int(10*q));pygame.draw.circle(s,fc,(x,y),int(7*q))
        for i,(sx,sy) in enumerate(reversed(self.snake)):
            idx=len(self.snake)-1-i;fade=idx/max(1,len(self.snake)-1);c=(int(30+45*(1-fade)),int(130+90*(1-fade)),int(70+55*(1-fade)))
            rr=pygame.Rect(BX+sx*CELL+2,BY+sy*CELL+2,CELL-4,CELL-4);pygame.draw.rect(s,(0,0,0),rr.move(2,3),border_radius=8);pygame.draw.rect(s,c,rr,border_radius=8)
        hx,hy=self.snake[0];cx,cy=center((hx,hy));dx,dy=self.d;px,py=-dy,dx
        for ex,ey in [(cx+dx*5+px*5,cy+dy*5+py*5),(cx+dx*5-px*5,cy+dy*5-py*5)]:
            pygame.draw.circle(s,WHITE,(int(ex),int(ey)),3);pygame.draw.circle(s,(5,10,15),(int(ex+dx),int(ey+dy)),1)
        pygame.draw.rect(s,(44,58,76),r,2,border_radius=14)
    def hud(self,s):
        text(s,"SNAKE // EVOLUTION",self.big,WHITE,(30,26));text(s,self.mode.upper()+" MODE",self.mono,GREEN,(32,75))
        x=600
        for a,b,c in [("SCORE",self.score,WHITE),("BEST",self.best,GOLD),("LEVEL",self.level,CYAN),("LENGTH",len(self.snake),GREEN)]:
            rr=pygame.Rect(x,26,125,58);pygame.draw.rect(s,PANEL,rr,border_radius=10);text(s,a,self.fs,MUTED,(x+12,34));text(s,str(b),self.f,c,(x+12,57));x+=135
        if self.combo>1:text(s,f"COMBO x{self.combo}",self.f,GOLD,(BX+10,BY+ROWS*CELL+17))
        if self.shield:text(s,"● SHIELD",self.fs,PURPLE,(BX+180,BY+ROWS*CELL+20))
        text(s,"WASD / ARROWS • P PAUSE • R RESTART • ESC MENU",self.fs,MUTED,(W-30,H-25),"bottomright")
        if self.msg_t:text(s,self.msg,self.big,GOLD,(W//2,BY+ROWS*CELL+18),"midtop")
    def background(self,s):
        for y in range(H):
            t=y/(H-1);c=tuple(int((8,12,20)[i]*(1-t)+(17,25,38)[i]*t) for i in range(3));pygame.draw.line(s,c,(0,y),(W,y))
    def menu(self,s):
        o=pygame.Surface((W,H),pygame.SRCALPHA);o.fill((3,7,12,150));s.blit(o,(0,0))
        text(s,"SNAKE",self.huge,GREEN,(W//2,120),"center");text(s,"EVOLUTION",self.big,WHITE,(W//2,178),"center");text(s,"A modern survival snake game",self.f,MUTED,(W//2,225),"center")
        for i,(k,t,d) in enumerate([("1","CLASSIC","Wrap-around • progressive difficulty"),("2","HARDCORE","Walls kill • more obstacles"),("3","SURVIVAL","Dense arena • relentless scaling")]):
            y=290+i*82;rr=pygame.Rect(W//2-270,y,540,68);pygame.draw.rect(s,PANEL,rr,border_radius=12);pygame.draw.rect(s,(45,62,78),rr,1,border_radius=12);pygame.draw.circle(s,GREEN if k=="1" else CYAN if k=="2" else (255,145,65),(rr.x+35,rr.centery),15);text(s,k,self.f,(8,12,20),(rr.x+35,rr.centery),"center");text(s,t,self.f,WHITE,(rr.x+65,rr.y+13));text(s,d,self.fs,MUTED,(rr.x+65,rr.y+40))
        text(s,"Press 1 / 2 / 3 to start",self.f,WHITE,(W//2,570),"center");text(s,f"BEST SCORE  {self.best}",self.f,GOLD,(W//2,650),"center")
    def over(self,s):
        o=pygame.Surface((W,H),pygame.SRCALPHA);o.fill((2,5,8,175));s.blit(o,(0,0))
        text(s,"GAME OVER",self.huge,RED,(W//2,245),"center");text(s,self.reason,self.f,MUTED,(W//2,305),"center");text(s,f"SCORE {self.score}",self.big,WHITE,(W//2,365),"center");text(s,f"BEST {self.best}",self.f,GOLD,(W//2,415),"center");text(s,"ENTER / R — PLAY AGAIN",self.f,GREEN,(W//2,490),"center");text(s,"ESC — MAIN MENU",self.fs,MUTED,(W//2,530),"center")
    def pause(self,s):
        o=pygame.Surface((W,H),pygame.SRCALPHA);o.fill((0,0,0,120));s.blit(o,(0,0));text(s,"PAUSED",self.huge,WHITE,(W//2,330),"center");text(s,"Press P to resume",self.f,MUTED,(W//2,395),"center")
    def draw(self,s):
        self.background(s);world=pygame.Surface((W,H),pygame.SRCALPHA);self.board(world);self.hud(world)
        q=int(self.shake);ox=random.randint(-q,q) if q else 0;oy=random.randint(-q,q) if q else 0;s.blit(world,(ox,oy))
        for p in self.parts:p.draw(s)
        if self.state=="menu":self.menu(s)
        elif self.state=="over":self.over(s)
        elif self.paused:self.pause(s)

def main():
    s=pygame.display.set_mode((W,H));pygame.display.set_caption("Snake Evolution");clock=pygame.time.Clock();g=Game();run=True
    while run:
        dt=min(clock.tick(FPS)/1000,.05)
        for e in pygame.event.get():
            if e.type==pygame.QUIT:run=False
            if e.type==pygame.KEYDOWN:
                k=e.key
                if g.state=="menu":
                    if k==pygame.K_1:g.mode="classic";g.start()
                    elif k==pygame.K_2:g.mode="hard";g.start()
                    elif k==pygame.K_3:g.mode="survival";g.start()
                    elif k==pygame.K_ESCAPE:run=False
                elif g.state=="playing":
                    if k in (pygame.K_UP,pygame.K_w):g.direction((0,-1))
                    elif k in (pygame.K_DOWN,pygame.K_s):g.direction((0,1))
                    elif k in (pygame.K_LEFT,pygame.K_a):g.direction((-1,0))
                    elif k in (pygame.K_RIGHT,pygame.K_d):g.direction((1,0))
                    elif k==pygame.K_p:g.paused=not g.paused
                    elif k==pygame.K_r:g.start()
                    elif k==pygame.K_ESCAPE:g.state="menu"
                else:
                    if k in (pygame.K_RETURN,pygame.K_r):g.start()
                    elif k==pygame.K_ESCAPE:g.state="menu"
        g.update(dt);g.draw(s);pygame.display.flip()
    g.save();pygame.quit()

if __name__=="__main__":main()
