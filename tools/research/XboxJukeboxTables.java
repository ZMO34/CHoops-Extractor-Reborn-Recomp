// Xbox executable evidence only; no source-platform addresses or tables.
// @category CHoops.Xbox
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.mem.*;
import java.io.*;

public class XboxJukeboxTables extends GhidraScript {
    private String text(long pointer) throws Exception {
        Address a=toAddr(pointer);StringBuilder result=new StringBuilder();
        for(int i=0;i<256;i++) {
            int c=Short.toUnsignedInt(currentProgram.getMemory().getShort(a.add(i*2)));
            if(c==0)return result.toString();
            if(c<32 || c>126)throw new IllegalArgumentException("Unexpected jukebox string");
            result.append((char)c);
        }
        throw new IllegalArgumentException("Unterminated jukebox string");
    }
    private long word(long address) throws Exception {return Integer.toUnsignedLong(currentProgram.getMemory().getInt(toAddr(address)));}
    private String quote(String value) {return "\""+value.replace("\\","\\\\").replace("\"","\\\"")+"\"";}
    public void run() throws Exception {
        long songs=0x84f983d8L,artists=0x84f99018L;
        try(PrintWriter out=new PrintWriter(new FileWriter(getScriptArgs()[0]))) {
            out.println("{\"platform\":\"xbox360\",\"songs_table\":\"84f983d8\",\"art_table\":\"84f99018\",\"tracks\":[");
            java.util.HashSet<Long> indices=new java.util.HashSet<>();
            java.util.HashMap<Long,Long> artRows=new java.util.HashMap<>();
            java.util.HashMap<String,Long> artGroups=new java.util.HashMap<>();
            for(int i=0;i<87;i++) {
                long art=artists+i*36;
                if(word(art+12)!=0x846ac6bcL)break;
                if(artRows.put(word(art+32),art)!=null)throw new IllegalArgumentException("Duplicate artist link");
                String bio=text(word(word(art+32)+16));
                Long prior=artGroups.put(bio,art);
                if(prior!=null && (!text(word(prior)).equals(text(word(art))) || !text(word(prior+8)).equals(text(word(art+8)))))throw new IllegalArgumentException("Ambiguous Xbox artist group");
            }
            for(int i=0;i<87;i++) {
                long row=songs+i*36+(i>=23?4:0),index=word(row),art=artRows.getOrDefault(row,artGroups.getOrDefault(text(word(row+16)),0L));
                if(index>=87 || !indices.add(index))throw new IllegalArgumentException("Jukebox row identity mismatch at "+i);
                String title=text(word(row+4)),bio=text(word(row+16)),artist=art==0?"":text(word(art)),cover=art==0?"":text(word(art+8)),bank=art==0?"cribmusic":text(word(art+12));
                if(art==0)throw new IllegalArgumentException("Missing Xbox artist/cover group");
                if(!bank.equals("cribmusic"))throw new IllegalArgumentException("Unexpected music bank");
                String category=bio.equals("BIO_FIGHT_SONGS")?"Band / Fight Songs":"Licensed Music";
                out.printf("%s{\"index\":%d,\"title\":%s,\"artist\":%s,\"cover_record\":%s,\"category\":%s,\"title_id\":\"%08x\"}%n",i==0?"":",",index,quote(title),quote(artist),quote(cover),quote(category),word(row+8));
            }
            out.println("]}");
        }
    }
}
