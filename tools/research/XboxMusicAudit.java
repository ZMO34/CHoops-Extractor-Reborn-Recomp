// @category CHoops.Xbox
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

public class XboxMusicAudit extends GhidraScript {
    public void run() throws Exception {
        try(PrintWriter out=new PrintWriter(new FileWriter(getScriptArgs()[0]))) {
            Memory memory=currentProgram.getMemory();
            for(String term:new String[]{"Til U Had Enough","Spit It Clearly","Hi Hi Yikas","Yea Alabama","You're Doing It","Time To Shine","cribmusic","fight song"}) {
                for(String encoding:new String[]{"UTF-8","UTF-16BE"}) {
                    byte[] pattern=term.getBytes(encoding);
                    for(MemoryBlock block:memory.getBlocks()) {
                        if(!block.isInitialized())continue;
                        Address match=memory.findBytes(block.getStart(),block.getEnd(),pattern,null,true,monitor);
                        if(match==null)continue;
                        out.println(term+" "+encoding+" "+match);
                        byte[] context=new byte[512];memory.getBytes(match.subtract(64),context);
                        out.println(new String(context,StandardCharsets.UTF_8).replace('\0','|'));
                        for(Reference ref:getReferencesTo(match))out.println("xref="+ref.getFromAddress());
                        long value=match.getOffset();byte[] pointer={(byte)(value>>24),(byte)(value>>16),(byte)(value>>8),(byte)value};
                        for(MemoryBlock candidate:memory.getBlocks()) {
                            if(!candidate.isInitialized())continue;
                            Address pos=candidate.getStart();int limit=0;
                            while(pos.compareTo(candidate.getEnd())<=0) {
                                Address ref=memory.findBytes(pos,candidate.getEnd(),pointer,null,true,monitor);
                                if(ref==null)break;
                                out.println("pointer="+ref);
                                for(int k=-8;k<16;k++)out.printf("  %s %08x%n",ref.add(k*4),memory.getInt(ref.add(k*4)));
                                if(++limit>=8)break;pos=ref.add(4);
                            }
                        }
                        out.flush();
                    }
                }
            }
        }
    }
}
