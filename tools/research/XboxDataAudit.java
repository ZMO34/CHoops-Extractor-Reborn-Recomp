// @category CHoops.Xbox
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import java.io.*;
import java.nio.file.*;
public class XboxDataAudit extends GhidraScript {
 private String text(long p) throws Exception {
  StringBuilder s=new StringBuilder();for(int i=0;i<128;i++){int c=Short.toUnsignedInt(currentProgram.getMemory().getShort(toAddr(p+i*2)));if(c==0)return s.toString();if(c<32||c>126)throw new Exception();s.append((char)c);}throw new Exception();
 }
 public void run() throws Exception {
  String[] args=getScriptArgs();Memory memory=currentProgram.getMemory();
  try(PrintWriter out=new PrintWriter(new FileWriter(args[0]))) {
   for(String line:Files.readAllLines(Path.of(args[1]))) {
    if(line.isBlank())continue;String[] words=line.trim().split(" +");long p=Long.parseUnsignedLong(words[0],16);int count=Integer.parseInt(words[1]);
    for(int i=0;i<count;i++){long at=p+i*4;long value=Integer.toUnsignedLong(memory.getInt(toAddr(at)));out.printf("%08x %08x",at,value);try{out.print(" text="+text(value));}catch(Exception e){}out.println();}
   }
  }
 }
}
