// @category CHoops.Xbox
import ghidra.app.script.GhidraScript;
import ghidra.program.model.mem.*;
import java.io.*;
public class XboxLeafFields extends GhidraScript {
 private int word(byte[] b,int p){return(b[p]&255)<<24|(b[p+1]&255)<<16|(b[p+2]&255)<<8|b[p+3]&255;}
 public void run() throws Exception {
  try(PrintWriter out=new PrintWriter(new FileWriter(getScriptArgs()[0]))) {
   for(MemoryBlock block:currentProgram.getMemory().getBlocks()) {
    if(!block.isInitialized()||!block.isExecute())continue;byte[] data=new byte[(int)block.getSize()];currentProgram.getMemory().getBytes(block.getStart(),data);
    for(int i=0;i+12<=data.length;i+=4){int a=word(data,i),b=word(data,i+4),c=word(data,i+8);int off=a&65535;
     if((a>>>26)==32&&(a>>>16&31)==3&&(off==0x90||off==0x98)&&(b>>>26)==21&&(b>>>16&31)==3&&c==0x4e800020)out.printf("getter=%s offset=%x shift=%d mb=%d me=%d%n",block.getStart().add(i),off,b>>>11&31,b>>>6&31,b>>>1&31);
    }
   }
  }
 }
}
