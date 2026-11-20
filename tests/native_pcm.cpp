#include "../runtime/native_pcm.h"
#include <cassert>
#include <iostream>

static void word(std::vector<uint8_t>& data,size_t pos,uint32_t value) {
  for(unsigned i=0;i<4;i++)data[pos+i]=uint8_t(value>>(i*8));
}
int main() {
  std::vector<uint8_t> wav(52,0);
  std::memcpy(wav.data(),"RIFF",4);word(wav,4,44);std::memcpy(wav.data()+8,"WAVEfmt ",8);
  word(wav,16,16);word(wav,20,1|(1<<16));word(wav,24,16000);word(wav,28,32000);word(wav,32,2|(16<<16));
  std::memcpy(wav.data()+36,"data",4);word(wav,40,8);
  wav[44]=0x34;wav[45]=0x12;wav[46]=0xfe;wav[47]=0xff;wav[48]=0;wav[49]=0x80;wav[50]=0xff;wav[51]=0x7f;
  auto clip=ch2k8::PCMClip::Parse(wav,1,16000,4);std::vector<uint8_t> output(12,0x77);clip.CopyBE(1,6,output);
  assert((output==std::vector<uint8_t>{0xff,0xfe,0x80,0,0x7f,0xff,0,0,0,0,0,0}));
  unsigned rejected=0;
  for(unsigned kind=0;kind<5;kind++) {
    auto corrupt=wav;
    if(kind==0)corrupt.pop_back();
    if(kind==1)word(corrupt,20,3|(1<<16));
    if(kind==2)word(corrupt,24,48000);
    if(kind==3)word(corrupt,40,7);
    if(kind==4)word(corrupt,16,1024);
    try{ch2k8::PCMClip::Parse(corrupt,1,16000,4);}catch(const std::runtime_error&){rejected++;}
  }
  assert(rejected==5);
  ch2k8::PCMStream stream;stream.Reset();stream.Observe(1,100);stream.Observe(1,50);
  assert(!stream.active());assert(!stream.Apply(output,1,1));stream.Reset();
  std::cout<<"Native PCM: endian, tail, truncation, codec, rate, extent and reset checks passed\n";
}
