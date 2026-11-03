// @category CHoops.Xbox
import ghidra.app.script.GhidraScript;
import ghidra.program.model.mem.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
public class XboxFunctionReferences extends GhidraScript {
 private int word(byte[] b,int p){return(b[p]&255)<<24|(b[p+1]&255)<<16|(b[p+2]&255)<<8|b[p+3]&255;}
 public void run() throws Exception {
  Set<Integer> wanted=new HashSet<>();for(String s:Files.readAllLines(Path.of(getScriptArgs()[1])))if(!s.isBlank())wanted.add((int)Long.parseUnsignedLong(s.trim(),16));
  try(PrintWriter out=new PrintWriter(new FileWriter(getScriptArgs()[0]))) {
   for(MemoryBlock block:currentProgram.getMemory().getBlocks()){
    if(!block.isInitialized()||block.isExecute())continue;byte[] data=new byte[(int)block.getSize()];currentProgram.getMemory().getBytes(block.getStart(),data);
    for(int i=0;i+4<=data.length;i+=4)if(wanted.contains(word(data,i))){out.printf("function=%08x reference=%s%n",word(data,i),block.getStart().add(i));for(int j=Math.max(0,i-48);j+4<=data.length&&j<=i+64;j+=4)out.printf("  %s %08x%n",block.getStart().add(j),word(data,j));}
   }
  }
 }
}
