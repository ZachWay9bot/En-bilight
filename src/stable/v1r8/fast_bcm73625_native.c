/* VU-Ambilight V1R7 native EXPERIMENT / BCM73625 only.
 * SPDX-License-Identifier: GPL-2.0-only
 * Decoder register / tile format derived from OpenPLi aio-grab (GPL-2.0).
 * This is not built or verified on actual VU hardware. ALL mmaps read-only.
 * No persistent installation, no decoder register writes, no Enigma2 changes.
 */
#define _GNU_SOURCE
#define _FILE_OFFSET_BITS 64
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <time.h>
#include <errno.h>

#define NLED 314
#define NSAMP 4
#define TILE 64U
#define REG_BASE ((off_t)0x10600000)
#define FPS 25
#define DDP_PORT 4048
#define HOSTFILE "/home/elight-addons/vu_ambilight/wled_host.txt"
#define ZONES "led_regions.txt"
#define MAXC 3

typedef struct {float h0,h1,v0,v1;} Zone;
typedef struct {uint32_t y,u,v;} Sample;
typedef struct {uint32_t stride,res,ofs,ofs2,adr,adr2;size_t leny,lenuv;} Info;
typedef struct {int used;uint32_t adr,adr2,stride,ofs,ofs2;unsigned char *ym,*uv;size_t leny,lenuv;uint64_t stamp;} Buf;
static Zone zones[NLED];
static Sample plans[NLED][NSAMP];
static uint32_t prev_stride,prev_res,prev_ofs,prev_ofs2;
static Buf caches[MAXC];
static uint64_t ticks;
static int mem_fd=-1;
static volatile unsigned char *regs;

static void die(const char *msg){fprintf(stderr,"R7 ABORT: %s\n",msg);exit(2);}
static int clamp(int v){return v<0?0:(v>255?255:v);}
static int64_t monotonic_ns(void){struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))die("clock_gettime");return (int64_t)t.tv_sec*1000000000LL+t.tv_nsec;}
static void msleep_ns(int64_t ns){if(ns>0){struct timespec t={ns/1000000000LL,ns%1000000000LL};nanosleep(&t,NULL);}}
static uint32_t tiled(uint32_t x,uint32_t y,uint32_t rows){return (x/TILE)*(rows*TILE)+y*TILE+((x%TILE)^3U);}
static void pixel_rgb(int Y,int U,int V,int *r,int *g,int *b){int c=298*(Y-16),d=U-128,e=V-128;*r=clamp((c+409*e+128)>>8);*g=clamp((c-100*d-208*e+128)>>8);*b=clamp((c+516*d+128)>>8);}
static void zones_read(const char *path){FILE *f=fopen(path,"r");if(!f)die("led_regions.txt fehlt");char line[256];int n=0;while(fgets(line,sizeof(line),f)){if(line[0]=='#'||line[0]=='\n')continue;float a,b,c,d;if(sscanf(line,"%f %f %f %f",&a,&b,&c,&d)!=4 || n>=NLED)die("Defekte LED-Zonen");if(!(a>=0&&b>a&&b<=1&&c>=0&&d>c&&d<=1))die("LED-Zone ausserhalb Bild");zones[n++]=(Zone){a,b,c,d};}fclose(f);if(n!=NLED)die("LED-Anzahl ungleich 314");}
static uint32_t read_yres(void){FILE *f=fopen("/proc/stb/vmpeg/0/yres","r");if(!f)die("yres fehlt");char line[64];if(!fgets(line,sizeof(line),f)){fclose(f);die("yres leer");}fclose(f);return (uint32_t)strtoul(line,NULL,16);}
static Info read_info(void){Info z;uint32_t a=0,b=0;
 z.stride=((uint32_t)regs[0x19]<<8)|regs[0x18]; z.ofs=(uint32_t)regs[0x3c+24]<<4;z.ofs2=(uint32_t)regs[0x3c+28]<<4;
 z.adr=((uint32_t)regs[0x37]<<24)|((uint32_t)regs[0x36]<<16)|((uint32_t)regs[0x35]<<8);
 z.adr2=((uint32_t)regs[0x3c+3]<<24)|((uint32_t)regs[0x3c+2]<<16)|((uint32_t)regs[0x3c+1]<<8);
 z.res=read_yres();a=(z.stride+TILE-1)/TILE;b=(uint32_t)getpagesize();
 if(z.stride<128||z.stride>2048||z.stride%16||z.res<64||z.res>1152||z.ofs<z.res||z.ofs>1216||z.ofs%16||z.ofs2<(z.res+1)/2||z.ofs2>608||z.ofs2%16)die("Decoder-Register unplausibel, sicherer Stopp");
 if(z.adr<0x1000000||z.adr2<0x1000000||z.adr>=0xF0000000||z.adr2>=0xF0000000||z.adr==z.adr2||z.adr%256||z.adr2%256)die("Decoder-Adressen unplausibel, sicherer Stopp");
 z.leny=(size_t)a*TILE*z.ofs+z.adr%b;z.lenuv=(size_t)a*TILE*z.ofs2+z.adr2%b;
 if(z.leny>3500000||z.lenuv>1800000)die("Decoder-Mapping zu gross");return z;}
static Buf *map_buffers(Info z){uint64_t now=++ticks;for(int i=0;i<MAXC;i++){Buf *p=&caches[i];if(p->used&&p->adr==z.adr&&p->adr2==z.adr2&&p->stride==z.stride&&p->ofs==z.ofs&&p->ofs2==z.ofs2){p->stamp=now;return p;}}
 int slot=-1;uint64_t oldest=UINT64_MAX;
 for(int i=0;i<MAXC;i++)if(!caches[i].used){slot=i;break;}
 if(slot<0)for(int i=0;i<MAXC;i++)if(caches[i].stamp<oldest){slot=i;oldest=caches[i].stamp;}
 Buf *p=&caches[slot];if(p->used){munmap(p->ym,p->leny);munmap(p->uv,p->lenuv);p->used=0;}
 int ps=getpagesize();unsigned char *ym=mmap(NULL,z.leny,PROT_READ,MAP_SHARED,mem_fd,(off_t)(z.adr&~(uint32_t)(ps-1)));
 if(ym==MAP_FAILED)die("luma mmap fehlgeschlagen");
 unsigned char *uv=mmap(NULL,z.lenuv,PROT_READ,MAP_SHARED,mem_fd,(off_t)(z.adr2&~(uint32_t)(ps-1)));
 if(uv==MAP_FAILED){munmap(ym,z.leny);die("chroma mmap fehlgeschlagen");}
 *p=(Buf){1,z.adr,z.adr2,z.stride,z.ofs,z.ofs2,ym,uv,z.leny,z.lenuv,now};return p;
}
static void plan_make(Info z){if(prev_stride==z.stride&&prev_res==z.res&&prev_ofs==z.ofs&&prev_ofs2==z.ofs2)return;
 const float xx[4]={0.25f,0.75f,0.25f,0.75f},yy[4]={0.25f,0.25f,0.75f,0.75f};
 for(int i=0;i<NLED;i++)for(int j=0;j<NSAMP;j++){
  uint32_t x=(uint32_t)((zones[i].h0+(zones[i].h1-zones[i].h0)*xx[j])*z.stride),y=(uint32_t)((zones[i].v0+(zones[i].v1-zones[i].v0)*yy[j])*z.res);
  if(x>=z.stride)x=z.stride-1;if(y>=z.res)y=z.res-1;
  uint32_t xpair=x&~1U;
  plans[i][j]=(Sample){tiled(x,y,z.ofs),tiled(xpair,y/2,z.ofs2),tiled(xpair+1,y/2,z.ofs2)};
 }
 prev_stride=z.stride;prev_res=z.res;prev_ofs=z.ofs;prev_ofs2=z.ofs2;
}
static void sample(Info z,Buf *p,unsigned char *out){uint32_t offy=z.adr%(uint32_t)getpagesize(),offuv=z.adr2%(uint32_t)getpagesize();
 for(int i=0;i<NLED;i++){int rs=0,gs=0,bs=0;for(int j=0;j<NSAMP;j++){Sample *s=&plans[i][j];int r,g,b;pixel_rgb(p->ym[offy+s->y],p->uv[offuv+s->u],p->uv[offuv+s->v],&r,&g,&b);rs+=r;gs+=g;bs+=b;}out[i*3]=(rs+2)/4;out[i*3+1]=(gs+2)/4;out[i*3+2]=(bs+2)/4;}}
static int ddp_socket(struct sockaddr_in *dst){char hostname[200],line[200];FILE*f=fopen(HOSTFILE,"r");if(!f)die("WLED host fehlt");if(!fgets(line,sizeof(line),f)){fclose(f);die("WLED Host leer");}fclose(f);if(sscanf(line,"%199s",hostname)!=1)die("WLED host ungültig");struct addrinfo hints={0},*res=NULL;hints.ai_family=AF_INET;hints.ai_socktype=SOCK_DGRAM;if(getaddrinfo(hostname,NULL,&hints,&res))die("WLED Host nicht aufloesbar");*dst=*(struct sockaddr_in*)res->ai_addr;dst->sin_port=htons(DDP_PORT);freeaddrinfo(res);int s=socket(AF_INET,SOCK_DGRAM,0);if(s<0)die("UDP socket fehlgeschlagen");return s;}
static void send_bri(struct sockaddr_in dst){int s=socket(AF_INET,SOCK_STREAM,0);if(s<0)return;dst.sin_port=htons(80);struct timeval t={1,0};setsockopt(s,SOL_SOCKET,SO_SNDTIMEO,&t,sizeof(t));setsockopt(s,SOL_SOCKET,SO_RCVTIMEO,&t,sizeof(t));if(connect(s,(void*)&dst,sizeof(dst))==0){const char *body="{\"on\":true,\"bri\":54}";char buf[256];int len=snprintf(buf,sizeof(buf),"POST /json/state HTTP/1.1\r\nHost: wled\r\nContent-Type: application/json\r\nContent-Length: %zu\r\nConnection: close\r\n\r\n%s",strlen(body),body);if(len>0&&(size_t)len<sizeof(buf))send(s,buf,len,0);}close(s);}
static void run(int live,int secs){FILE *chip=fopen("/proc/stb/info/chipset","r");char str[128]={0};if(!chip||!fgets(str,sizeof(str),chip)||!strstr(str,"73625"))die("Nur BCM73625 erlaubt");fclose(chip);
 mem_fd=open("/dev/mem",O_RDONLY|O_SYNC);if(mem_fd<0)die("/dev/mem nicht lesbar");regs=mmap(NULL,4096,PROT_READ,MAP_SHARED,mem_fd,REG_BASE);if(regs==MAP_FAILED)die("BCM register mmap fehlgeschlagen");
 int sock=-1;struct sockaddr_in dst;memset(&dst,0,sizeof(dst));if(live){sock=ddp_socket(&dst);send_bri(dst);}
 unsigned char pkt[952]={0},last[942]={0};pkt[0]=0x41;pkt[2]=1;pkt[3]=1;pkt[8]=3;pkt[9]=174;
 int n=0,changed=0;double busy=0;int64_t start=monotonic_ns(),next=start,lastprint=start;
 printf("V1R7 Native %s: Ziel %d Hz, %d LEDs, maximal %ds. Raw-RGB ohne Gamma/Saettigung.\n",live?"LIVE":"PROBE",FPS,NLED,secs);fflush(stdout);
 while(monotonic_ns()-start<(int64_t)secs*1000000000LL){int64_t t=monotonic_ns();Info z=read_info();Buf*p=map_buffers(z);plan_make(z);sample(z,p,pkt+10);busy+=(monotonic_ns()-t)/1e9;
  if(n&&memcmp(last,pkt+10,942))changed++;memcpy(last,pkt+10,942);
  if(sock>=0){pkt[1]=(unsigned char)(n&255);if(sendto(sock,pkt,952,0,(void*)&dst,sizeof(dst))<0)die("DDP sendto fehlgeschlagen");}
  n++;int64_t now=monotonic_ns();if(now-lastprint>=2000000000LL){double elapsed=(now-start)/1e9;int rs=0,gs=0,bs=0;for(int q=0;q<NLED;q++){rs+=last[q*3];gs+=last[q*3+1];bs+=last[q*3+2];}printf("%.1fs frames=%d %.1f/s changes=%d avg %u/%u/%u compute %.2fms\n",elapsed,n,n/elapsed,changed,rs/NLED,gs/NLED,bs/NLED,busy*1000/n);fflush(stdout);lastprint=now;}
  next+=1000000000LL/FPS;int64_t delay=next-monotonic_ns();if(delay>0)msleep_ns(delay);else next=monotonic_ns();
 }
 double elapsed=(monotonic_ns()-start)/1e9;printf("END %.2f FPS daten=%d veraendert=%d/%d compute=%.2fms; echte 25 FPS nur bei entsprechenden Aenderungen nachgewiesen\n",n/elapsed,n,changed,n>0?n-1:0,busy*1000/(n?n:1));
 if(n>10&&changed<=1)fprintf(stderr,"WARNUNG: Quelle liefert wahrscheinlich eingefrorenes Bild!\n");
 for(int i=0;i<MAXC;i++)if(caches[i].used){munmap(caches[i].ym,caches[i].leny);munmap(caches[i].uv,caches[i].lenuv);}
 if(sock>=0)close(sock);munmap((void*)regs,4096);close(mem_fd);
}
static void selftest(void){if(tiled(64,0,64)!=4099||tiled(0,0,64)!=3||tiled(1,0,64)!=2)die("Tiling-Test fehlgeschlagen");int r,g,b;pixel_rgb(16,128,128,&r,&g,&b);if(r||g||b)die("YUV test black");pixel_rgb(235,128,128,&r,&g,&b);if(r!=255||g!=255||b!=255)die("YUV test white");puts("SELFTEST PASS: tile offsets / RGB math");}
int main(int argc,char**argv){int live=0,secs=12,ack=0;for(int i=1;i<argc;i++){if(!strcmp(argv[i],"--selftest")){selftest();return 0;}else if(!strcmp(argv[i],"--live"))live=1;else if(!strcmp(argv[i],"--probe"))live=0;else if(!strcmp(argv[i],"--ack-wled"))ack=1;else if(!strcmp(argv[i],"--seconds")&&i+1<argc)secs=atoi(argv[++i]);else {fprintf(stderr,"Usage: %s [--selftest | --probe | --live --ack-wled] [--seconds N]\n",argv[0]);return 2;}}
 if(live&&!ack)die("Live erfordert --ack-wled und gestoppten Pi-Hyperion");if(secs<3)secs=3;if(secs>30)secs=30;
 zones_read(ZONES);run(live,secs);return 0;}
