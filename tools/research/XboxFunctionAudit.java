// @category CHoops.Xbox
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.io.*;
import java.nio.file.*;
public class XboxFunctionAudit extends GhidraScript {
 public void run() throws Exception {
  String[] args=getScriptArgs();DecompInterface decompiler=new DecompInterface();decompiler.openProgram(currentProgram);
  try(PrintWriter out=new PrintWriter(new FileWriter(args[0]))) {
   for(String line:Files.readAllLines(Path.of(args[1]))) {
    if(line.isBlank())continue;Address address=toAddr(Long.parseUnsignedLong(line.trim(),16));Function f=getFunctionAt(address);
    if(f==null){disassemble(address);f=createFunction(address,null);}
    out.println("requested="+address);
    if(f!=null){DecompileResults r=decompiler.decompileFunction(f,30,monitor);if(r.decompileCompleted())out.println(r.getDecompiledFunction().getC());}
    InstructionIterator instructions=currentProgram.getListing().getInstructions(address,true);int n=0;
    while(instructions.hasNext() && n++<128){Instruction i=instructions.next();out.println(i.getAddress()+" "+i);if(i.getFlowType().isTerminal())break;}
   }
  } finally{decompiler.dispose();}
 }
}
