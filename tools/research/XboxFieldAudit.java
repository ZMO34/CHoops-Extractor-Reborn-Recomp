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
            // Caption registrations are DWORD aligned. Index all requested IDs
            // in one bounded pass instead of rescanning the executable per ID.
            java.util.HashMap<Long,java.util.List<Address>> matches=new java.util.HashMap<>();
            for(long id:ids)matches.put(id,new java.util.ArrayList<>());
            for(MemoryBlock block:memory.getBlocks()) {
                if(!block.isInitialized())continue;
                final int chunkSize=4*1024*1024;
                for(long offset=0;offset<block.getSize();offset+=chunkSize) {
                    monitor.checkCancelled();int size=(int)Math.min(chunkSize,block.getSize()-offset);byte[] chunk=new byte[size];memory.getBytes(block.getStart().add(offset),chunk);
                    for(int at=0;at+3<size;at+=4) {
                        long value=(long)(chunk[at]&255)<<24 | (long)(chunk[at+1]&255)<<16 | (long)(chunk[at+2]&255)<<8 | chunk[at+3]&255;
                        java.util.List<Address> hits=matches.get(value);
                        if(hits!=null && hits.size()<16)hits.add(block.getStart().add(offset+at));
                    }
                }
            }
            for(long id:ids) {
                out.printf("caption=%08x%n",id);
                out.flush();
                for(Address match:matches.get(id)) {
                        MemoryBlock block=memory.getBlock(match);
                        if(match.subtract(block.getStart())<12 || match.add(60).compareTo(block.getEnd())>0)continue;
                        out.println("match="+match);
                        if(memory.getInt(match.subtract(8))==2) {
                            int maximum=memory.getInt(match.add(52));long options=Integer.toUnsignedLong(memory.getInt(match.add(56)));
                            MemoryBlock optionBlock=memory.getBlock(toAddr(options));
                            if(maximum>=0 && maximum<256 && optionBlock!=null && !optionBlock.isExecute()) {
                                out.printf("options_max=%d table=%08x%n",maximum,options);
                                for(int option=0;option<=maximum;option++)out.printf("option=%d id=%08x%n",option,memory.getInt(toAddr(options+option*4)));
                            }
                        }
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
                }
            }
            decompiler.dispose();
        }
    }
}
