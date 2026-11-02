// Read-only Xbox native field/caption audit. Outputs remain private.
// @category CHoops.Xbox
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import ghidra.app.decompiler.*;
import java.util.HashSet;

public class XboxFieldAudit extends GhidraScript {
    public void run() throws Exception {
        String[] args=getScriptArgs();
        if(args.length<1)throw new IllegalArgumentException("Output filename required");
        try(PrintWriter out=new PrintWriter(new FileWriter(args[0]))) {
            out.println("program="+currentProgram.getName());
            out.println("language="+currentProgram.getLanguageID());
            out.println("compiler="+currentProgram.getCompilerSpec().getCompilerSpecID());
            Memory memory=currentProgram.getMemory();
            DecompInterface decompiler=new DecompInterface();
            decompiler.openProgram(currentProgram);
            HashSet<Long> inspected=new HashSet<>();
            long[] ids={0x0f3173fa5L,0x0b3aac31L,0x08040a689L,0x0298c9b35L,0x0b2753bf5L,0x0694b364bL};
            if(args.length>1) {
                java.util.List<String> lines=java.nio.file.Files.readAllLines(java.nio.file.Path.of(args[1]));
                ids=new long[lines.size()];for(int i=0;i<ids.length;i++)ids[i]=Long.parseUnsignedLong(lines.get(i).trim(),16);
            }
            for(long id:ids) {
                byte[] pattern={(byte)(id>>24),(byte)(id>>16),(byte)(id>>8),(byte)id};
                out.printf("caption=%08x%n",id);
                out.flush();
                int found=0;
                for(MemoryBlock block:memory.getBlocks()) {
                    if(!block.isInitialized())continue;
                    Address pos=block.getStart();
                    while(pos.compareTo(block.getEnd())<=0) {
                        Address match=memory.findBytes(pos,block.getEnd(),pattern,null,true,monitor);
                        if(match==null)break;
                        out.println("match="+match);
                        Address from=match.subtract(Math.min(32,match.subtract(block.getStart())));
                        for(int k=0;k<24;k++) {
                            Address a=from.add(k*4);
                            if(a.compareTo(block.getEnd().subtract(3))>0)break;
                            int value=memory.getInt(a);out.printf("  %s %08x",a,value);
                            Address pointer=toAddr(Integer.toUnsignedLong(value));
                            Function function=getFunctionAt(pointer);
                            MemoryBlock code=memory.getBlock(pointer);
                            if(function==null && code!=null && code.isExecute() && (value&3)==0) {
                                disassemble(pointer);function=createFunction(pointer,null);
                            }
                            if(function!=null)out.print(" function="+function.getName());
                            out.println();
                            if(function!=null && inspected.add(Integer.toUnsignedLong(value))) {
                                DecompileResults result=decompiler.decompileFunction(function,30,monitor);
                                if(result.decompileCompleted())out.println(result.getDecompiledFunction().getC());
                                else out.println("decompile_error="+result.getErrorMessage());
                            }
                        }
                        for(Reference reference:getReferencesTo(match))out.println("xref="+reference.getFromAddress());
                        if(++found>=16)break;
                        pos=match.add(1);
                    }
                    if(found>=16)break;
                }
            }
            decompiler.dispose();
        }
    }
}
