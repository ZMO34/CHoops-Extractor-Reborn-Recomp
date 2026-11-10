import io,json,struct,wave
from types import SimpleNamespace
import pytest
from choops_recomp import audio


def wav(value):
    out=io.BytesIO()
    with wave.open(out,'wb') as stream:stream.setparams((1,2,16000,0,'NONE',''));stream.writeframes(bytes([value,0])*4)
    return out.getvalue()


def setup(tmp_path):
    assets=tmp_path/'assets';assets.mkdir();export=tmp_path/'export';export.mkdir();resources={};rows=[]
    for i in range(2):
        key=f'a/{i}';folder=assets/str(i);folder.mkdir();blocks=[struct.pack('>11I',1,5,2,4,16000,0,2048,0,0,0,0),bytes([i])*2048]
        r=SimpleNamespace(key=key,label='Track '+str(i),folder=folder,blocks=lambda blocks=blocks:blocks,record=dict(index=i));resources[key]=r
        (folder/'audio.wav').write_bytes(wav(3));(folder/'audio.json').write_bytes(b'old marker')
        (export/f'{i}.wav').write_bytes(wav(7));rows.append(dict(resource=key,file=f'{i}.wav',source_identity=audio.info(blocks)['source_identity'],wav_sha256=audio.sha(wav(3))))
    (export/'audio_manifest.json').write_text(json.dumps(dict(version=1,platform='xbox360',tracks=rows)))
    w=SimpleNamespace(root=tmp_path,assets=assets,manifest=dict(storage='loose-resources'),resource=lambda key:resources[key],require=lambda feature:None)
    return w,export,resources


def test_batch_selection_and_unchanged_exports(tmp_path):
    w,folder,resources=setup(tmp_path);review=audio.review_batch(w,folder)
    assert len(review)==2
    assert audio.apply_batch(w,folder,review[:1])==1
    assert (resources['a/0'].folder/'audio.wav').read_bytes()==wav(7)
    assert (resources['a/1'].folder/'audio.wav').read_bytes()==wav(3)
    (folder/'1.wav').write_bytes(wav(3));assert [r['resource'] for r in audio.review_batch(w,folder)]==['a/0']
    assert not list(tmp_path.glob('.studio-audio-*'))


def test_batch_rejects_changes_after_review_before_writing(tmp_path):
    w,folder,resources=setup(tmp_path);review=audio.review_batch(w,folder)
    (folder/'1.wav').write_bytes(wav(8))
    with pytest.raises(ValueError,match='changed since review'):audio.apply_batch(w,folder,review)
    assert all((r.folder/'audio.wav').read_bytes()==wav(3) for r in resources.values())


def test_batch_write_failure_restores_preceding_audio_and_markers(tmp_path,monkeypatch):
    w,folder,resources=setup(tmp_path);review=audio.review_batch(w,folder);write=audio.atomic_write
    def fail(path,payload,expected=None):
        if path==resources['a/1'].folder/'audio.wav':raise OSError('simulated disk failure')
        return write(path,payload,expected)
    monkeypatch.setattr(audio,'atomic_write',fail)
    with pytest.raises(OSError,match='disk failure'):audio.apply_batch(w,folder,review)
    assert all((r.folder/'audio.wav').read_bytes()==wav(3) and (r.folder/'audio.json').read_bytes()==b'old marker' for r in resources.values())
    assert not list(tmp_path.glob('.studio-audio-*'))
