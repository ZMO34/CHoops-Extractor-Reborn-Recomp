// @category CHoops.Xbox
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.listing.*;
import java.io.*;
import java.util.*;

public class XboxPackedFieldAudit extends GhidraScript {
    private int word(byte[] b,int p){return (b[p]&255)<<24|(b[p+1]&255)<<16|(b[p+2]&255)<<8|b[p+3]&255;}
    public void run() throws Exception {
        Memory memory=currentProgram.getMemory();Map<MemoryBlock,byte[]> blocks=new HashMap<>();List<Address> targets=new ArrayList<>();
        try(PrintWriter out=new PrintWriter(new FileWriter(getScriptArgs()[0]))) {
            for(MemoryBlock block:memory.getBlocks()) {
                if(!block.isInitialized() || !block.isExecute())continue;
                byte[] data=new byte[(int)block.getSize()];memory.getBytes(block.getStart(),data);blocks.put(block,data);
                for(int i=0;i+12<data.length;i+=4) {
                    int load=word(data,i),rotate=word(data,i+4);
                    if((load>>>26)!=32 || (load&65535)!=0x84 || (rotate>>>26)!=21 || (rotate>>>11&31)!=15 || (rotate>>>6&31)!=28 || (rotate>>>1&31)!=31 || (load>>>21&31)!=(rotate>>>21&31))continue;
                    Address a=block.getStart().add(i);out.println("candidate_class_getter="+a+" next="+Integer.toHexString(word(data,i+8)));targets.add(a);
                }
            }
            DecompInterface decompiler=new DecompInterface();decompiler.openProgram(currentProgram);
            for(Address target:targets) {
                Function function=getFunctionAt(target);
                if(function==null){disassemble(target);function=createFunction(target,null);}
                if(function!=null){DecompileResults result=decompiler.decompileFunction(function,30,monitor);if(result.decompileCompleted())out.println(result.getDecompiledFunction().getC());}
                for(var block:blocks.entrySet()) {
                    byte[] data=block.getValue();
                    for(int i=0;i+4<=data.length;i+=4) {
                        int instruction=word(data,i);if((instruction>>>26)!=18 || (instruction&2)!=0)continue;
                        int delta=(instruction&0x03fffffc);if((delta&0x02000000)!=0)delta|=0xfc000000;
                        Address site=block.getKey().getStart().add(i);
                        if(!site.add(delta).equals(target))continue;
                        out.println("caller_site="+site);Function caller=getFunctionContaining(site);
                        if(caller!=null){DecompileResults result=decompiler.decompileFunction(caller,30,monitor);if(result.decompileCompleted())out.println(result.getDecompiledFunction().getC());}
                    }
                }
            }
            decompiler.dispose();
        }
    }
}
