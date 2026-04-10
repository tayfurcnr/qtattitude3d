# qtattitude3d

[![PyPI version](https://img.shields.io/pypi/v/qtattitude3d-kairos)](https://pypi.org/project/qtattitude3d-kairos/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

`qtattitude3d`, PyQt5 uygulamaları için optimize edilmiş, PyVista ve VTK tabanlı yüksek performanslı bir 3B yönelim (attitude) görselleştirme kütüphanesidir. Yer istasyonları ve telemetri panelleri için modern bir çözüm sunar.

## Kurulum

### Hızlı Kurulum (PyPI)

```bash
pip install qtattitude3d-kairos
```

### Kaynak Koddan Kurulum

```bash
git clone https://github.com/tayfurcnr/qtattitude3d.git
cd qtattitude3d
pip install -e .
```

## Paket Ne Sağlar?

- PyQt5 içine eklenebilen hazır bir 3B widget
- `OBJ + MTL` model yükleme desteği
- Roll, pitch, yaw açılarını programatik olarak uygulama
- Başlangıç kamera ayarlarını dışarıdan verme
- Modelin başlangıç ölçeğini dışarıdan ayarlama
- Hazır tema seçenekleri arasında geçiş yapma
- Render kalitesini performans ihtiyacına göre seçme
- Kamera görünümü ve yakınlaştırma düzeyini koddan yönetme
- Arka plan, grid, eksen ve zemin görünümünü kontrol etme
- Paket içinden çalışan sade bir demo pencere
- GUI olmayan ortamlarda kontrollü hata mesajı

## Paket Yapısı

- `widgets/`
  Ana kullanıcı bileşenleri. `QtAttitude3DWidget` burada bulunur.
- `io/`
  `OBJ + MTL` yükleme ve sahne hazırlama kodları.
- `models/`
  Paket içinde kullanılan veri modelleri.
- `core/`
  Paket içi yol yardımcıları ve çalışma zamanı kontrolleri.
- `demo/`
  Demo penceresi ve demo giriş noktası.
- `assets/`
  Paketle birlikte gelen örnek model dosyaları.

## Dışarı Açık API

Paket kökünden doğrudan kullanılabilen isimler:

```python
from qtattitude3d import (
    QtAttitude3DWidget,
    QtAttitudeDemoWindow,
    PACKAGE_ROOT,
    ASSETS_DIR,
    get_asset_path,
    get_demo_model_path,
)
```

### `QtAttitude3DWidget`

Ana 3B widget sınıfıdır. Bir PyQt5 layout içine doğrudan eklenebilir.

Kurucu parametreleri:

- `parent`
  Standart PyQt ebeveyn widget referansı.
- `background`
  Arka plan rengi. Tek renk verilebilir ya da iki elemanlı tuple/list ile gradyan tanımlanabilir.
  Örnek:
  `"#0f172a"` veya `("#08111f", "#1b2b45")`
- `grid_color`
  Grid çizgilerinin rengi.
- `show_grid`
  Widget açıldığında grid görünür mü.
- `show_axes`
  Widget açıldığında eksen göstergesi görünür mü.
- `camera_position`
  Başlangıç kamera konumu.
  Biçim:
  `[(kamera_x, kamera_y, kamera_z), (odak_x, odak_y, odak_z), (up_x, up_y, up_z)]`
- `initial_angles`
  Başlangıç roll, pitch, yaw değerleri.
  Biçim:
  `(roll, pitch, yaw)`
- `model_scale`
  Modelin başlangıç ölçek katsayısı.
  `1.0` normal ölçektir.
  `1.25`, `1.5`, `2.0` gibi değerlerle model başlangıçta daha büyük görünür.
- `theme`
  Hazır görünüm teması.
  Varsayılan tema `midnight` değeridir.
  Mevcut temalar:
  `midnight`, `dark`, `light`, `sunset`
- `render_quality`
  Render kalitesi profili.
  Mevcut değerler:
  `performance`, `balanced`, `quality`
  Varsayılan değer `balanced`tir.

Örnek kullanım:

```python
from qtattitude3d import QtAttitude3DWidget

widget = QtAttitude3DWidget(
    background=("#08111f", "#1b2b45"),
    grid_color="#6b7c93",
    show_grid=True,
    show_axes=True,
    camera_position=[(18, 12, 14), (0, 0, 0), (0, 0, 1)],
    initial_angles=(0.0, 0.0, 0.0),
    model_scale=1.25,
    theme="midnight",
    render_quality="balanced",
)
```

### `QtAttitude3DWidget` Methodları

#### `load_model(path)`

Verilen `OBJ` modelini yükler.  
Modelin yanında referans verilen `MTL` dosyası da kullanılır.

- Girdi:
  `path` -> `str` veya `Path`
- Dönüş:
  `True` veya `False`

Örnek:

```python
widget.load_model("/tam/yol/model.obj")
```

#### `load_scene(scene)`

Önceden hazırlanmış sahne nesnesini doğrudan widget içine yükler.  
Bu yöntem daha çok paket içi ya da ileri seviye kullanım içindir.

#### `set_angles(roll, pitch, yaw, degrees=True)`

Modele anlık açı uygular.
Bu metod, açıları içsel olarak Quaterniona dönüştürerek "Gimbal Lock" oluşmasını engeller.

- `roll`
  X ekseni etrafındaki dönüş (Yatış)
- `pitch`
  Y ekseni etrafındaki dönüş (Yunuslama)
- `yaw`
  Z ekseni etrafındaki dönüş (Sapma)

**Not:** Eksenler havacılık standartlarına (NED - North East Down) göre eşleştirilmiştir. Eğer modeliniz ters dönüyorsa açı değerlerini `-` ile çarpmanız gerekebilir.

Örnek:

```python
widget.set_angles(roll=10.0, pitch=5.0, yaw=45.0)
```

#### `set_camera_position(position)`

Kamerayı yeni bir başlangıç/çalışma pozisyonuna alır.

Örnek:

```python
widget.set_camera_position([(14, 10, 12), (0, 0, 0), (0, 0, 1)])
```

#### `zoom_camera(factor)`

Kamerayı mevcut bakış açısından yakınlaştırır veya uzaklaştırır.

- `1.2` gibi bir değer yakınlaştırır.
- `0.8` gibi bir değer uzaklaştırır.

Örnek:

```python
widget.zoom_camera(1.2)
widget.zoom_camera(0.8)
```

#### `set_camera_view(view_name)`

Hazır kamera görünümü uygular.

Kullanılabilir görünümler:

- `isometric`
- `front`
- `top`
- `right`

Örnek:

```python
widget.set_camera_view("top")
```

#### `set_model_scale(scale)`

Modelin ölçek katsayısını değiştirir.  
Eğer model yüklenmişse yeniden yüklenerek yeni ölçek uygulanır.

Örnek:

```python
widget.set_model_scale(1.6)
```

#### `set_background(color)`

Arka plan rengini değiştirir.

- Tek renk:
  `"#101826"`
- Gradyan:
  `("#08111f", "#1b2b45")`

#### `set_theme(theme_name)`

Hazır tema uygular. Bu işlem arka plan, grid ve zemin görünümünü birlikte günceller.

Kullanılabilir temalar:

- `midnight`
- `dark`
- `light`
- `sunset`

Örnek:

```python
widget.set_theme("light")
```

#### Render kalite profilleri

- `performance`
  En akıcı profil. Görsel kalite bir miktar düşer ama etkileşim daha rahattır.
- `balanced`
  Günlük kullanım için önerilen dengeli profil.
- `quality`
  En yüksek kalite profili. Özellikle büyük modellerde daha fazla ekran kartı maliyeti oluşturur.

#### `set_render_quality(render_quality)`

Render kalite profilini çalışma anında değiştirir.

Örnek:

```python
widget.set_render_quality("performance")
```

#### `set_grid_visible(visible)`

Grid görünürlüğünü açar veya kapatır.

Örnek:

```python
widget.set_grid_visible(False)
```

#### `set_grid_color(color)`

Grid rengini değiştirir.

Örnek:

```python
widget.set_grid_color("#475569")
```

#### `set_axes_visible(visible)`

Eksen göstergesini açar veya kapatır.

#### `set_floor_visible(visible)`

Arka plandaki zemin düzlemini açar veya kapatır.

#### `reset_camera()`

Kamerayı mevcut başlangıç ayarına göre sıfırlar.

#### `get_scene_stats()`

Yüklenen sahne hakkında özet bilgi döndürür.

Örnek dönüş:

```python
{
    "group_count": 40,
    "face_count": 473462,
    "vertex_count": 672484,
    "source_path": "/tam/yol/model.obj",
}
```

### `QtAttitude3DWidget` Sinyalleri

#### `modelLoaded`

Model başarıyla yüklendiğinde yayılır.  
Parametre olarak yüklenen dosyanın tam yolunu taşır.

#### `modelLoadFailed`

Model yüklenemediğinde yayılır.  
Parametre olarak hata mesajını taşır.

Örnek:

```python
widget.modelLoaded.connect(print)
widget.modelLoadFailed.connect(print)
```

## `QtAttitudeDemoWindow`

Paketle birlikte gelen örnek pencere sınıfıdır.  
İçinde:

- sol tarafta roll / pitch / yaw kontrolleri
- tema ve render kalitesi seçim alanları
- kamera görünümü ve yakınlaştırma düğmeleri
- sağ tarafta `QtAttitude3DWidget`

bulunur.

Kurucu parametreleri:

- `model_path`
  Açılışta yüklenecek model yolu
- `window_title`
  Pencere başlığı
- `window_size`
  Başlangıç pencere boyutu, örnek: `(1400, 900)`
- `background`
- `grid_color`
- `show_grid`
- `show_axes`
- `camera_position`
- `initial_angles`
- `model_scale`
- `theme`
- `render_quality`

Örnek:

```python
from qtattitude3d import QtAttitudeDemoWindow

window = QtAttitudeDemoWindow(
    window_title="Yer İstasyonu Demo",
    window_size=(1400, 900),
    show_grid=True,
    show_axes=True,
    camera_position=[(18, 12, 14), (0, 0, 0), (0, 0, 1)],
    model_scale=1.25,
    theme="sunset",
    render_quality="performance",
)
```

Ek method:

#### `set_window_size(width, height)`

Demo penceresinin (stand-alone) boyutunu değiştirir. Ana uygulamalarda pencere yönetimi ana pencere (QMainWindow/QWidget) üzerinden yapılmalıdır.

## Yardımcı Yol Fonksiyonları

### `PACKAGE_ROOT`

Paket kök dizinini verir.

### `ASSETS_DIR`

Paket içindeki `assets/` dizinini verir.

### `get_asset_path(name)`

Paket içindeki bir asset’in tam yolunu verir.

Örnek:

```python
from qtattitude3d import get_asset_path

obj_path = get_asset_path("example/Drone.obj")
```

### `get_demo_model_path()`

Paketle birlikte gelen demo modelinin tam yolunu verir.

## Temel Kullanım Örneği

Bir PyQt5 penceresi içine widget eklemek için:

```python
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from qtattitude3d import QtAttitude3DWidget, get_demo_model_path


class AnaPencere(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.attitude_widget = QtAttitude3DWidget(
            show_grid=True,
            show_axes=True,
            model_scale=1.25,
            theme="midnight",
            render_quality="balanced",
        )
        layout.addWidget(self.attitude_widget)

        self.attitude_widget.load_model(get_demo_model_path())
        self.attitude_widget.set_angles(roll=5.0, pitch=10.0, yaw=20.0)
```

## Demo Çalıştırma

Paket demosunu çalıştırmak için:

```bash
python3 -m qtattitude3d
```

GUI olmayan ortamlarda paket çökmez; bunun yerine temiz bir açıklama mesajı vererek çıkar.

## Notlar

- Mouse ile sahne üzerinde yakınlaşma, uzaklaşma ve döndürme yapılabilir.
- Demo penceresinde tema seçimi yapılabilir.
- `camera_position`, başlangıç kadrajını belirler.
- `model_scale`, modelin sahnedeki başlangıç ölçeğini belirler.
- `theme`, arka plan ve sahne stilini hızlıca değiştirir.
- `render_quality`, görüntü kalitesi ile akıcılık arasındaki dengeyi belirler.
- İkisi birbirinden farklıdır ve birlikte kullanılabilir.
