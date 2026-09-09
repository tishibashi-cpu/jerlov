# Examples

Two scripts. Both run against the installed package and need nothing beyond
NumPy.

```
python examples/sources_disagree.py
python examples/synthetic_underwater_images.py
```

They are run by CI on every push, so an example that has stopped working is a
failed build rather than something a reader discovers.

## `sources_disagree.py`

Why `jerlov.water()` makes you name a source.

The same Jerlov water type has different coefficients in different papers.
At 510 nm the scattering coefficient of Jerlov III differs by a factor of
**3.8** between the two published sets. A visibility estimate, a synthetic
image, or a fitted attenuation coefficient built on one is not comparable with
one built on the other.

The script also shows what each source says is doubtful about itself, what
happens at the cells a published table got wrong, and the three things the
package refuses to guess.

## `synthetic_underwater_images.py`

Turning an above-water spectrum into what it would look like at depth: the
thing papers on underwater vision need for training data, and the thing that
usually gets done with hard-coded coefficients.

Prints, as terminal colour blocks, how five reflectance patches appear at
ranges from 0 to 16 m in Jerlov III water at 15 m depth, white-balanced two
ways — to daylight, which keeps the water's cast, and to the downwelling
irradiance at depth, which removes it. Then the veiling fraction, the
contrast, and coefficients in the Akkaynak-Treibitz form.

**It ends with the limits, and they are not small.** The backscatter ratio was
stated rather than derived; the veiling radiance came from an estimate whose
geometry is an approximation; the path is horizontal and the target
Lambertian; the surface spectrum is CIE D65 rather than a measurement; the
reflectance spectra are smooth inventions. Every one of those is a choice a
caller can replace with a measurement.

None of it has been compared against photographs, because the measurements
needed to do that do not appear to exist. The output is what the published
coefficients imply, not a prediction.
