// ============================================================
// PCM AUDIO WORKLET
//
// Input:
//   Browser/WebRTC audio, typically 48 kHz float32
//
// Output:
//   16 kHz mono signed 16-bit PCM
//
// Chunks:
//   100 ms
// ============================================================

class PCMProcessor extends AudioWorkletProcessor {

    constructor(options) {

        super();

        const processorOptions =
            options.processorOptions || {};

        this.targetSampleRate =
            processorOptions.targetSampleRate || 16000;

        this.chunkMs =
            processorOptions.chunkMs || 100;

        this.inputSampleRate =
            sampleRate;

        this.resampleRatio =
            this.inputSampleRate /
            this.targetSampleRate;

        this.targetChunkSamples =
            Math.round(
                this.targetSampleRate *
                this.chunkMs /
                1000
            );


        // ----------------------------------------------------
        // Resampling buffer
        // ----------------------------------------------------

        this.inputBuffer = [];

        this.inputPosition = 0;


        // ----------------------------------------------------
        // Output buffer
        // ----------------------------------------------------

        this.outputBuffer = [];


        console.log(
            "[PCM WORKLET] Started",
            {
                inputSampleRate:
                    this.inputSampleRate,

                targetSampleRate:
                    this.targetSampleRate,

                resampleRatio:
                    this.resampleRatio,

                targetChunkSamples:
                    this.targetChunkSamples
            }
        );
    }


    process(inputs, outputs) {

        const input =
            inputs[0];

        const output =
            outputs[0];


        // ----------------------------------------------------
        // No input
        // ----------------------------------------------------

        if (
            !input ||
            !input[0] ||
            input[0].length === 0
        ) {

            return true;
        }


        // ----------------------------------------------------
        // Mono channel
        //
        // Jitsi audio is normally mono for speech.
        // If more channels are present, we use channel 0.
        // ----------------------------------------------------

        const channel =
            input[0];


        for (
            let i = 0;
            i < channel.length;
            i++
        ) {

            this.inputBuffer.push(
                channel[i]
            );
        }


        // ----------------------------------------------------
        // Resample
        //
        // Linear interpolation.
        // ----------------------------------------------------

        while (
            this.inputPosition + 1 <
            this.inputBuffer.length
        ) {

            const index =
                Math.floor(
                    this.inputPosition
                );

            const fraction =
                this.inputPosition -
                index;


            const sample1 =
                this.inputBuffer[index];

            const sample2 =
                this.inputBuffer[index + 1];


            const sample =
                sample1 +
                (
                    sample2 -
                    sample1
                ) *
                fraction;


            this.outputBuffer.push(
                sample
            );


            this.inputPosition +=
                this.resampleRatio;


            // ------------------------------------------------
            // Emit a 100 ms PCM chunk
            // ------------------------------------------------

            if (
                this.outputBuffer.length >=
                this.targetChunkSamples
            ) {

                this.emitPCM();
            }
        }


        // ----------------------------------------------------
        // Remove samples that were fully consumed.
        // ----------------------------------------------------

        const samplesToRemove =
            Math.floor(
                this.inputPosition
            );


        if (
            samplesToRemove > 0
        ) {

            this.inputBuffer =
                this.inputBuffer.slice(
                    samplesToRemove
                );

            this.inputPosition -=
                samplesToRemove;
        }


        // ----------------------------------------------------
        // Pass the audio through.
        //
        // The main graph sends it through a gain node set
        // to zero, so nothing is played.
        // ----------------------------------------------------

        if (
            output &&
            output[0]
        ) {

            const outputChannel =
                output[0];


            const copyLength =
                Math.min(
                    outputChannel.length,
                    channel.length
                );


            for (
                let i = 0;
                i < copyLength;
                i++
            ) {

                outputChannel[i] =
                    channel[i];
            }
        }


        return true;
    }


    // ========================================================
    // EMIT PCM
    // ========================================================

    emitPCM() {

        const sampleCount =
            this.targetChunkSamples;


        if (
            this.outputBuffer.length <
            sampleCount
        ) {

            return;
        }


        const floatSamples =
            this.outputBuffer.splice(
                0,
                sampleCount
            );


        const int16Samples =
            new Int16Array(
                sampleCount
            );


        for (
            let i = 0;
            i < sampleCount;
            i++
        ) {

            let sample =
                floatSamples[i];


            // ------------------------------------------------
            // Clamp
            // ------------------------------------------------

            sample =
                Math.max(
                    -1,
                    Math.min(
                        1,
                        sample
                    )
                );


            // ------------------------------------------------
            // Float32 → Int16
            // ------------------------------------------------

            if (
                sample < 0
            ) {

                int16Samples[i] =
                    sample * 32768;

            } else {

                int16Samples[i] =
                    sample * 32767;
            }
        }


        // ----------------------------------------------------
        // Send transferable ArrayBuffer
        // ----------------------------------------------------

        this.port.postMessage(
            {
                type: "pcm",
                sampleRate:
                    this.targetSampleRate,
                channels: 1,
                format: "s16le",
                buffer:
                    int16Samples.buffer
            },
            [
                int16Samples.buffer
            ]
        );
    }
}


// ============================================================
// REGISTER
// ============================================================

registerProcessor(
    "pcm-processor",
    PCMProcessor
);