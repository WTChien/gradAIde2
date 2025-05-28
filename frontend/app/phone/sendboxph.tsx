"use client";
import React from 'react';
import '../style.css';
import Image from 'next/image';

export default function SendBoxph() {

    const handleInput = (e: React.FormEvent<HTMLTextAreaElement>) => {
        const textarea = e.target as HTMLTextAreaElement;
        textarea.style.height = "24px"; // 重置高度，確保自動調整
        textarea.style.height = `${Math.min(textarea.scrollHeight, 123)}px`; // 最大高度限制 72px (3行高)
    };


    return (
        <>
                <textarea
                    className="sendbox"
                    name='question'
                    onInput={(e) => handleInput(e)}
                    style={{height:'2.4em'}}
                >
                </textarea>
                <button className="send-button"><Image alt='' className='sendicon' src='/img/clip.png' /></button>
                <button className='voice' style={{marginLeft:'25px'}}><Image alt='' className='voiceicon' src='/img/Group.png' /></button>
        </>
    )
}