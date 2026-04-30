import pygame, sys, random
from collections import deque
from dataclasses import dataclass

DISPLAY_W, DISPLAY_H, TILE, FPS = 900, 600, 60, 20
ROWS, COLS = DISPLAY_H // TILE, DISPLAY_W // TILE
BLACK, SAND, DIAMOND, GOLD, UNBOXED, PLAYER, AGENT, DEAD = range(8)
GOLD_DELAY_FRAMES, GOLD_FALL_FRAMES, MAX_AGENTS, AGENT_SPAWN_INTERVAL = 4, 10, 3, FPS * 5
NOBBIN_TO_HOBBIN_MIN, HOBBIN_DURATION, AGENT_BASE_DELAY = FPS * 8, FPS * 6, 7

@dataclass
class Agent:
    r: int
    c: int
    kind: str = "nobbin"
    state_timer: int = 0
    freeze: int = 0
    move_timer: int = 0

class Data:
    def __init__(self):
        try:
            self.player = pygame.image.load(r'materials\player.png').convert_alpha()
            self.sand = pygame.image.load(r'materials\sand.png').convert_alpha()
            self.gold = pygame.image.load(r'materials\gold.png').convert_alpha()
            self.diamond = pygame.image.load(r'materials\diamond.png').convert_alpha()
            self.agent = pygame.image.load(r'materials\agent.png').convert_alpha()
            self.unboxed = pygame.image.load(r'materials\unboxed_gold.png').convert_alpha()
            self.black = pygame.image.load(r'materials\black_space.png').convert_alpha()
            self.dead = pygame.image.load(r'materials\dead_player.png').convert_alpha()
        except Exception:
            self.player = pygame.Surface((TILE,TILE), pygame.SRCALPHA); pygame.draw.circle(self.player,(0,120,255),(TILE//2,TILE//2),TILE//2-4)
            self.sand = pygame.Surface((TILE,TILE)); self.sand.fill((194,178,128))
            self.gold = pygame.Surface((TILE,TILE)); self.gold.fill((212,175,55))
            self.diamond = pygame.Surface((TILE,TILE)); self.diamond.fill((0,200,200))
            self.agent = pygame.Surface((TILE,TILE)); self.agent.fill((200,60,60))
            self.unboxed = pygame.Surface((TILE,TILE)); self.unboxed.fill((255,165,0))
            self.black = pygame.Surface((TILE,TILE)); self.black.fill((10,10,30))
            self.dead = pygame.Surface((TILE,TILE)); self.dead.fill((100,100,100))
        self.scale()
    def scale(self):
        imgs = [self.black, self.sand, self.diamond, self.gold, self.unboxed, self.player, self.agent, self.dead]
        scaled = [pygame.transform.scale(i,(TILE,TILE)) for i in imgs]
        self.black, self.sand, self.diamond, self.gold, self.unboxed, self.player, self.agent, self.dead = scaled
    def get(self, tile):
        return {BLACK:self.black,SAND:self.sand,DIAMOND:self.diamond,GOLD:self.gold,UNBOXED:self.unboxed,PLAYER:self.player,AGENT:self.agent,DEAD:self.dead}[tile]

class DiggerRemake:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((DISPLAY_W, DISPLAY_H))
        pygame.display.set_caption("Digger")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 20)
        self.data = Data()
        self.matrix = [
            [0,1,1,1,3,1,1,1,1,1,0,0,0,0,0],
            [0,1,1,2,2,1,1,2,1,1,0,1,3,1,1],
            [0,3,1,2,2,1,1,2,1,1,0,1,1,1,1],
            [0,1,1,2,2,3,1,2,3,1,0,1,2,2,2],
            [0,1,1,2,2,1,1,2,1,1,0,1,2,2,2],
            [0,0,1,2,2,1,1,2,1,1,0,1,2,2,2],
            [1,0,1,1,1,1,3,1,3,1,0,1,1,1,1],
            [1,0,0,0,0,1,1,1,1,1,0,1,1,1,1],
            [2,1,1,1,0,1,1,1,1,1,0,1,1,1,2],
            [2,2,1,1,0,0,0,5,0,0,0,1,1,2,2]
        ]
        self.player_pos = [9,7]
        self.player_dir = "right"
        self.matrix[self.player_pos[0]][self.player_pos[1]] = PLAYER
        self.gold_states = {}
        for r in range(ROWS):
            for c in range(COLS):
                if self.matrix[r][c] == GOLD:
                    self.gold_states[(r,c)] = {'delay':0,'falling':False,'fall_frame':0}
                    #dictionary dotor durin r, c bairlald
        self.falling_golds, self.agents, self.frame = [], [], 0
        #falling_golds unaj bui altni medeelliig hadgalna.
        #agentvvdiin medeelliig hadgalah list
        #heden frame ongorsoniig toolno. zarim uildel todorhoi tooni frame soligdsoni daraa hiigdeh tul 
        self.agent_spawn_timer, self.player_move_count, self.score, self.lives = 0,0,0,3
        #agentiin toroh hugatsaani tooluur neg agent vvseed todorhoi hugatsaani daraa daraagiin agent vvsne. player move_count ni tuhain toglogchiig heden vildel hiisniig toolno. score onoog  tootsno ene baihgui baisnch bolno. self.lives toglogchiin niit hojigdoh bolomjiig toolno.
        self.game_over_flag = False # togloom duussan esehiig hadgalna.
        self.spawn_initial_agents() # agentuudiig vvsgeh function
    def spawn_initial_agents(self): # togloomin ehend 1 shine agent vvsgeh
        for y,x in [(0,14),(0,13),(0,12)]: # agentiig edgeer gurvan bairlalin ali hoosn deer ni vvsgne
            if self.matrix[y][x]==BLACK: # hervee hooson baival
                a=Agent(y,x,"nobbin",0,0,random.randint(0,AGENT_BASE_DELAY)) # nobbin torliin agent vvsgne
                self.agents.append(a);self.matrix[y][x]=AGENT;return
                #vvsgesen agentaa agents listed append hiine, mon shine agentiin bairlalig matrixd nemj ogno tegeed return hiine gehdee utga butsaahgui
    def try_spawn_agent(self): #togloltin ywtsad busad agentuudig vvsgeh
        if self.game_over_flag:return False #hervee toglolt duussan baival false 
        self.agent_spawn_timer+=1 #frame bvrt negeer nemegduulne. todorhoi frame ongorsonii daraa agent vvsgne.
        if self.agent_spawn_timer>=AGENT_SPAWN_INTERVAL and len(self.agents)<MAX_AGENTS:
            #100framed agent shineer vvsne oiroltsoogoor 5 second bas niit  vvssen agent < 3
            for y,x in random.sample([(0,14),(0,13),(0,12)], 3):
                if self.matrix[y][x]==BLACK:
                    #hervee tuhain random bairlal deer hoosn baival agentaa vvsgne. 
                    a=Agent(y,x,"nobbin",0,0,random.randint(0,AGENT_BASE_DELAY))
                    # a object bvhii shine agent vvsgne
                    self.agents.append(a);self.matrix[y][x]=AGENT;self.agent_spawn_timer=0;return True
                    #agentiig agents listdee nemeed bairlalig bvrtgeed shine agent dongoj say vvssen tul spawn timer iig 0 bolgono.
            self.agent_spawn_timer=0
        return False #agent vvsgej chadaagui bol false utga butsaana
    def move_player(self, dr, dc, push=True): #dr rowiin huwid hiisn hodolgoon dc columnii huwid hiisne hodolgoon
        if self.game_over_flag:
            return False # toglolt duussan baivl false
        r, c = self.player_pos # toglogchiin odoogiin bairlaliig avna
        nr, nc = r + dr, c + dc # hodolgooniig nemeed shine bairlalig vvsgne.
        if not (0 <= nr < ROWS and 0 <= nc < COLS): #herwee hyazgaaraas hetrvvlheer vildel baival false butsaana
            return False
        #columnii huvid hiij bui hodologoon eyreg baival x++ baival baruun
        if dc > 0:
            self.player_dir = "right"
        #columnii huwid hiij bui hodolgoon sorog baival x-- baival zvvn
        elif dc < 0:
            self.player_dir = "left"
        #row iin huwid hiij bui hodolgoon eyreg baival y++ doosh
        elif dr > 0:
            self.player_dir = "down"
        #y-- baiwal deer hodolj baina gej tootsno.
        elif dr < 0:
            self.player_dir = "up"

        target = self.matrix[nr][nc] # toglogchiin shineer ochih bairlal deer baigaa zviliin medeelel 

        if dc != 0 and target == GOLD:
            bc = nc + dc  #altni daraagiin bairlal
            if 0 <= bc < COLS and self.matrix[nr][bc] in (BLACK, SAND, DIAMOND):
                #alt tvregdeh
                self.matrix[nr][bc] = GOLD
                #altni shine bairlalig oruulah
                if (nr, nc) in self.gold_states:
                    self.gold_states[(nr, bc)] = self.gold_states.pop((nr, nc))
                else:
                    self.gold_states[(nr, bc)] = {'delay': 0, 'falling': False, 'fall_frame': 0}
                self.matrix[r][c] = BLACK
                self.player_pos = [nr, nc]
                self.matrix[nr][nc] = PLAYER
                self.player_move_count += 1
                #tvlhegdsen altni door hooson baival unana
                if nr + 1 < ROWS and self.matrix[nr + 1][bc] == BLACK:
                    self.start_falling(nr, bc)
                return True
            return False
        
        if target == GOLD:
            return False
        if target in (BLACK, SAND, DIAMOND, UNBOXED):
            if target == DIAMOND:
                self.score += 25
            elif target == UNBOXED:
                self.score += 500
            self.matrix[r][c] = BLACK
            self.player_pos = [nr, nc]
            if self.matrix[nr][nc] == AGENT:
                self.matrix[nr][nc] = DEAD
                self.game_over()
                return True
            self.matrix[nr][nc] = PLAYER
            self.player_move_count += 1
            return True
        return False


    def dig(self):
        if self.game_over_flag:return False
        dr,dc=0,0
        if self.player_dir=="up":dr=-1
        elif self.player_dir=="down":dr=1
        elif self.player_dir=="left":dc=-1
        elif self.player_dir=="right":dc=1
        y,x=self.player_pos[0]+dr,self.player_pos[1]+dc
        if not(0<=y<ROWS and 0<=x<COLS):return False
        if self.matrix[y][x]==SAND:self.matrix[y][x]=BLACK;return True
        if self.matrix[y][x]==GOLD:self.matrix[y][x]=UNBOXED;self.gold_states.pop((y,x),None);return True
        return False
    def build_dijkstra(self):
        INF=10**6;dist=[[INF]*COLS for _ in range(ROWS)]
        q=deque();py,px=self.player_pos;dist[py][px]=0;q.append((py,px))
        while q:
            y,x=q.popleft()
            for dy,dx in((0,1),(1,0),(0,-1),(-1,0)):
                ny,nx=y+dy,x+dx
                if 0<=ny<ROWS and 0<=nx<COLS and self.matrix[ny][nx]in(BLACK,UNBOXED)and dist[ny][nx]>dist[y][x]+1:
                    dist[ny][nx]=dist[y][x]+1;q.append((ny,nx))
        return dist
    def start_falling(self,r,c):
        if (r,c)in self.gold_states:self.gold_states.pop((r,c),None)
        self.falling_golds.append({'r':r,'c':c,'frame':0})


    def update_gold(self):
        # alt bvriin huwid unaj bui frame delay iig hynah
        if not hasattr(self, 'gold_fall_frames'):
            self.gold_fall_frames = {}

        new_falling = []  #unaj bui altnuud
        for fg in self.falling_golds:
            r, c = fg['r'], fg['c']
            fg['frame'] += 1  # frame counter iig nemegduuleh
            if fg['frame'] < 8:  #altig 8n frame tutamd neg hodolgoh vildel hiij baina.
                new_falling.append(fg)
                continue

            #frame 8 bolood ng hodolchihvol dahiad shineer ehlne
            fg['frame'] = 0
            below_r, below_c = r + 1, c

            # herwee alt hamgiin dood mor buyu tsonhni dood tal ochwol unboxed bolno
            if below_r >= ROWS:
                self.matrix[r][c] = UNBOXED
                continue

            below = self.matrix[below_r][below_c]

            #door ni hoosn buyu black baival doosh unagaaasaar l baina.
            if below == BLACK:
                self.matrix[r][c] = BLACK
                self.matrix[below_r][below_c] = GOLD
                fg['r'] += 1
                new_falling.append(fg)

            # door ni agent baival ustgana
            elif below == AGENT:
                for a in list(self.agents):
                    if a.r == below_r and a.c == below_c:
                        self.agents.remove(a)
                        self.score += 250
                        break
                self.matrix[r][c] = BLACK
                self.matrix[below_r][below_c] = GOLD
                fg['r'] += 1
                new_falling.append(fg)

            #door ni toglogch baival alt darj alaad game over bolno.
            elif below == PLAYER:
                self.matrix[below_r][below_c] = DEAD
                self.matrix[r][c] = BLACK
                self.game_over()
                return

            # door ni els diamond eswel unboxed baival gazardaad zadarna.
            elif below in (SAND, DIAMOND, UNBOXED):
                self.matrix[r][c] = UNBOXED

        # falling golds iig shinechlene yagaad gewel alt hodolson
        self.falling_golds = new_falling

        # Odoogoor unaagvi bolowch unah magadlaltai altig haina.
        for r in range(ROWS - 2, -1, -1):  # доороос дээш шалгах
            for c in range(COLS):
                if self.matrix[r][c] == GOLD:
                    #hervee ter altin doorh hooson buyu dood hesgiig uhaad awchihsan baiwal alt doosh unana.
                    below_r = r + 1
                    if self.matrix[below_r][c] == BLACK:
                        #unaj ehleh
                        self.falling_golds.append({'r': r, 'c': c, 'frame': 0})


    def adjust_agent_delay(self):return AGENT_BASE_DELAY
    
    def move_agents(self):
        if self.game_over_flag:return
        for a in self.agents:
            a.state_timer+=1
            if a.kind=="nobbin"and a.state_timer>=NOBBIN_TO_HOBBIN_MIN and random.random()<0.02:a.kind="hobbin";a.state_timer=0;a.freeze=2
            elif a.kind=="hobbin"and a.state_timer>=HOBBIN_DURATION:a.kind="nobbin";a.state_timer=0;a.freeze=2
        #hervee 
        if self.frame%3==0 or not hasattr(self,"dist_cache"):self.dist_cache=self.build_dijkstra()
        dist=self.dist_cache
        for a in self.agents:
            if 0<=a.r<ROWS and 0<=a.c<COLS and self.matrix[a.r][a.c]==AGENT:self.matrix[a.r][a.c]=BLACK
        new,occ=[],set()
        for a in self.agents:
            if a.move_timer==0:a.move_timer=random.randint(0,AGENT_BASE_DELAY)
            a.move_timer-=1
            if a.move_timer>0:new.append(a);occ.add((a.r,a.c));continue
            a.move_timer=self.adjust_agent_delay()
            if a.freeze>0:
                a.freeze-=1;
                new.append(a)
                occ.add((a.r,a.c)) # occ tuhain agentiin bairlal 
                continue
            #bd = dijkstragiin tootsoolson odoogiin bairlalin zai(best distance)
            ay,ax=a.r,a.c;best=None;bd=dist[ay][ax]if 0<=ay<ROWS and 0<=ax<COLS else 10**6
            for dy,dx in[(0,1),(1,0),(0,-1),(-1,0)]:
                ny,nx=ay+dy,ax+dx
                if not(0<=ny<ROWS and 0<=nx<COLS):continue
                #toglogchtoi dawhtswal duusna.
                if[ny,nx]==self.player_pos:self.matrix[ny][nx]=DEAD;self.game_over();return
                #ali bairlal hooson baina geed bolomjtoig  songoh
                if self.matrix[ny][nx]in(BLACK, UNBOXED)and dist[ny][nx]<bd and(ny,nx)not in occ:bd=dist[ny][nx];best=(ny,nx)
                #hobbin uyd elsiig ch uhah tul sand eshiig shalgah
                #bd daraagiin bairlal ni toglogchruu oir baina uu eswel yg odoogiin bairlal ni oir baina uu gej shalgana
                elif a.kind=="hobbin"and self.matrix[ny][nx]==SAND and dist[ny][nx]<bd and(ny,nx)not in occ:bd=dist[ny][nx];best=(ny,nx)
            if best:
                ny,nx=best
                if a.kind=="hobbin"and self.matrix[ny][nx]==SAND:self.matrix[ny][nx]=BLACK;a.freeze=1
                a.r,a.c=ny,nx;new.append(a);occ.add((ny,nx))
            else:new.append(a);occ.add((ay,ax))
        self.agents=new
        for a in self.agents:
            if[a.r,a.c]==self.player_pos:self.matrix[a.r][a.c]=DEAD;self.game_over();return
            if self.matrix[a.r][a.c]in(BLACK,UNBOXED):self.matrix[a.r][a.c]=AGENT
    def check_win(self):
        for r in self.matrix:
            if DIAMOND in r:return False
        return True
    def game_over(self):self.game_over_flag=True
    def render(self):
        self.screen.fill((0,0,0))
        for r in range(ROWS):
            for c in range(COLS):
                t=self.matrix[r][c]
                if t not in(BLACK,SAND,DIAMOND,GOLD,UNBOXED,PLAYER,AGENT,DEAD):t=BLACK
                img=self.data.get(t)
                if t==PLAYER:
                    if self.player_dir=="left":img=pygame.transform.flip(img,True,False)
                    elif self.player_dir=="up":img=pygame.transform.rotate(img,90)
                    elif self.player_dir=="down":img=pygame.transform.rotate(img,-90)
                self.screen.blit(img,(c*TILE,r*TILE))
        hud_y=ROWS*TILE
        pygame.draw.rect(self.screen,(30,30,30),(0,hud_y,DISPLAY_W,DISPLAY_H-hud_y))
        self.screen.blit(self.font.render(f"Score: {self.score}   Lives: {self.lives}   Agents: {len(self.agents)}/{MAX_AGENTS}",True,(255,255,255)),(8,hud_y+6))
        if self.game_over_flag:
            o=pygame.Surface((DISPLAY_W,DISPLAY_H),pygame.SRCALPHA);o.fill((0,0,0,180));self.screen.blit(o,(0,0))
            t=self.font.render("GAME OVER",True,(255,80,80));self.screen.blit(t,(DISPLAY_W//2-60,DISPLAY_H//2))
        pygame.display.flip()
    def run(self):
        s=False
        while True:
            self.clock.tick(FPS);self.frame+=1
            for e in pygame.event.get():
                if e.type==pygame.QUIT:pygame.quit();sys.exit()
                if e.type==pygame.KEYDOWN:
                    if e.key in(pygame.K_LSHIFT,pygame.K_RSHIFT):s=True
                    elif e.key==pygame.K_SPACE:self.dig()
                    elif e.key==pygame.K_UP:self.move_player(-1,0,push=s)
                    elif e.key==pygame.K_DOWN:self.move_player(1,0,push=s)
                    elif e.key==pygame.K_LEFT:self.move_player(0,-1,push=s)
                    elif e.key==pygame.K_RIGHT:self.move_player(0,1,push=s)
                    elif e.key==pygame.K_RETURN and self.game_over_flag:self.__init__()
                if e.type==pygame.KEYUP:
                    if e.key in(pygame.K_LSHIFT,pygame.K_RSHIFT):s=False
            if not self.game_over_flag:
                self.try_spawn_agent();self.update_gold();self.move_agents()
                if self.check_win():
                    self.screen.fill((0,0,0));m=self.font.render("Ta yallaa",True,(255,215,0));self.screen.blit(m,(DISPLAY_W//2-140,DISPLAY_H//2));pygame.display.flip();pygame.time.wait(1500);pygame.quit();sys.exit()
            self.render()

if __name__=="__main__":DiggerRemake().run() 